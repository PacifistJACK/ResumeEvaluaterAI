from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz  # This is PyMuPDF
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def pdf_to_base64_image(file_bytes):
    """Converts the first page of a PDF to a base64 encoded JPEG image."""
    try:
        # Open the PDF from memory
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) < 1:
            return None
            
        # Get the first page
        page = doc.load_page(0) 
        
        # Take a screenshot (Pixmap)
        # matrix=fitz.Matrix(2, 2) makes the image 2x larger (clearer for AI)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        
        # Convert to bytes
        img_bytes = pix.tobytes("jpeg")
        
        # Encode to base64 string
        base64_str = base64.b64encode(img_bytes).decode('utf-8')
        return base64_str
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None

@app.post("/analyze")
async def analyze_resume_vision(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # 1. Read file bytes
    file_content = await file.read()
    
    # 2. Convert to Image
    base64_image = pdf_to_base64_image(file_content)
    if not base64_image:
        raise HTTPException(status_code=400, detail="Could not convert PDF to image")

    # 3. Define the Vision Prompt
    system_prompt = """
    You are an expert recruiter. Look at the resume image provided.
    Evaluate BOTH the content (skills, experience) AND the visual presentation (formatting, whitespace, font choice).
    
    You MUST respond with this exact JSON structure:
    {
        "score": (integer 0-100),
        "goodPoints": ["string", "string"],
        "badPoints": ["string", "string"],
        "recommendations": ["string", "string"]
    }
    """

    # 4. Payload with IMAGE DATA
    payload = {
        "model": "qwen/qwen-2.5-vl-7b-instruct:free", # Vision Capable Model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        ai_content = response.json()["choices"][0]["message"]["content"]
        
        # Clean JSON markdown if present
        cleaned_content = ai_content.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_content)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="AI Processing Failed")

# Run with: uvicorn main:app --reload