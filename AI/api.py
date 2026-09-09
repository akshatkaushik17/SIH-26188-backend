from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from AI.processor import analyze_document
from AI.database import save_scan_result, get_scan_history

app = FastAPI(
    title="SIH26188 Document Verification API",
    description="AI document processing API for SIH prototype",
    version="1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://projectsih-sigma.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "SIH26188 Document Verification API is running"
    }


@app.post("/analyze")
async def analyze(
    document: UploadFile = File(...),
    face: UploadFile = File(None)
):

    # Save document
    document_path = "uploaded_document.png"

    with open(document_path, "wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    # Save face image if provided
    face_path = None

    if face is not None:
        face_path = "uploaded_face.png"

        with open(face_path, "wb") as buffer:
            shutil.copyfileobj(face.file, buffer)

    # Run AI pipeline
    try:
        result = analyze_document(
            document_path,
            face_path
        )

    finally:

        # Delete document
        if os.path.exists(document_path):
            os.remove(document_path)

        # Delete face image
        if face_path is not None:
            if os.path.exists(face_path):
                os.remove(face_path)

    # Save analysis to verification history
    scan_id = save_scan_result(result)

    # Include scan ID in API response
    result["scan_id"] = scan_id

    # Return result
    return result


@app.get("/history")
def history():

    return get_scan_history()
