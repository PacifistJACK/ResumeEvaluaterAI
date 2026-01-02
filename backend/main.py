from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import requests
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://resume210.onrender.com/",
        "https://resume210.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def pdf_to_base64_image(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) < 1:
            return None
        page = doc.load_page(0) 
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        img_bytes = pix.tobytes("jpeg")
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None

@app.post("/analyze")
async def analyze_resume_vision(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    file_content = await file.read()
    base64_image = pdf_to_base64_image(file_content)
    
    if not base64_image:
        raise HTTPException(status_code=400, detail="Could not convert PDF to image")

    system_prompt = """
    You are an expert recruiter. Look at the resume image provided.
    Evaluate BOTH the content and the visual presentation.
    Return ONLY a JSON object with: score (0-100), goodPoints (list), badPoints (list), recommendations (list).
    """

   
    payload = {
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ]
    }

    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resume210.onrender.com/",
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        ai_content = response.json()["choices"][0]["message"]["content"]
        
        
        cleaned_content = ai_content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_content)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e)}")