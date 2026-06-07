from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import httpx  # Non-blocking async HTTP client
import base64
import json
import os
from dotenv import load_dotenv

# ================== CONFIG ==================
load_dotenv()

API_KEY = os.getenv("API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback to "google/gemini-2.5-flash" (or use "openrouter/free" to auto-route to a free vision model)
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-2.5-flash")

if not API_KEY:
    raise RuntimeError("API_KEY not found in environment variables")

# ================== APP ==================
app = FastAPI(title="Resume Evaluator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://resume210.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000"  # Included for local frontend development flexibility
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== HELPERS ==================
def pdf_to_base64_image(file_bytes: bytes) -> str | None:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) == 0:
            return None

        # Process the first page
        page = doc.load_page(0)
        # Using matrix 2x2 yields high quality rendering of text for the vision LLM
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("jpeg")

        return base64.b64encode(img_bytes).decode("utf-8")

    except Exception as e:
        print("PDF ERROR:", e)
        return None


def safe_json_parse(text: str):
    """
    Attempts to safely extract JSON from AI output.
    Prevents server crashes.
    """
    try:
        # Remove markdown fences
        cleaned = text.replace("```json", "").replace("```", "").strip()

        # Extract JSON block if extra text exists
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found")

        return json.loads(cleaned[start:end + 1])

    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return {
            "score": 0,
            "goodPoints": [],
            "badPoints": ["AI returned invalid JSON"],
            "recommendations": ["Try again or upload a clearer resume"]
        }

# ================== ROUTES ==================
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Resume Evaluator API running"
    }


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_bytes = await file.read()
    image_b64 = pdf_to_base64_image(file_bytes)

    if not image_b64:
        raise HTTPException(status_code=400, detail="Could not process PDF")

    prompt = """
You are an expert resume reviewer. Critically assess the provided resume to determine if it is professionally ready. Your review should focus primarily on the quality and relevance of the content, considering content to be slightly more important than the overall structure and design.

Return ONLY valid JSON.
NO explanations.
NO markdown.

JSON format:
{
  "score": 0-100,
  "goodPoints": [],
  "badPoints": [],
  "recommendations": []
}
"""

    payload = {
        "model": "google/gemma-4-31b-it:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resume210.onrender.com",
    }

    try:
        # Using non-blocking httpx inside async route
        async with httpx.AsyncClient() as client:
            res = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60.0
            )

        res.raise_for_status()
        res_json = res.json()

        # Check for errors in the OpenRouter response object structure
        if "choices" not in res_json or not res_json["choices"]:
            error_details = res_json.get("error", {})
            error_msg = error_details.get("message", "Unknown API error from OpenRouter")
            print("OPENROUTER ERROR:", error_msg)
            return {
                "score": 0,
                "goodPoints": [],
                "badPoints": [f"AI Service Error: {error_msg}"],
                "recommendations": ["Verify your API Key / OpenRouter balance or try again later"]
            }

        ai_text = res_json["choices"][0]["message"]["content"]
        return safe_json_parse(ai_text)

    except httpx.HTTPStatusError as e:
        print("OPENROUTER HTTP ERROR:", e.response.text)
        return {
            "score": 0,
            "goodPoints": [],
            "badPoints": [f"AI service returned HTTP error: {e.response.status_code}"],
            "recommendations": ["Verify your API Key / OpenRouter credits or try again later"]
        }
    except Exception as e:
        print("API CALL ERROR:", e)
        return {
            "score": 0,
            "goodPoints": [],
            "badPoints": ["AI service unavailable or network error"],
            "recommendations": ["Please try again later"]
        }


@app.get("/health")
def health():
    return {"status": "ok"}
