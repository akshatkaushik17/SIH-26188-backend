from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

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


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
@app.post("/test-upload")
async def test_upload(document: UploadFile = File(...)):
    data = await document.read()
    return {
        "filename": document.filename,
        "size": len(data),
        "content_type": document.content_type
    }
@app.get("/test-easyocr-import")
def test_easyocr_import():
    try:
        import easyocr
        return {
            "status": "EasyOCR import OK",
            "version": easyocr.__version__
        }
    except Exception as e:
        return {
            "status": "EasyOCR import failed",
            "error": str(e)
        }
@app.get("/test-torch")
def test_torch():
    try:
        import torch
        return {
            "status": "Torch OK",
            "version": torch.__version__
        }
    except Exception as e:
        return {
            "status": "Torch failed",
            "error": str(e)
        }
@app.get("/test-model-files")
def test_model_files():
    import os

    model_dir = os.path.join(
        os.path.dirname(__file__),
        "models"
    )

    files = os.listdir(model_dir)

    return {
        "status": "Model directory OK",
        "files": files,
        "sizes": {
            f: os.path.getsize(os.path.join(model_dir, f))
            for f in files
        }
    }
@app.get("/test-ai")
def test_ai():
    import traceback

    try:
        from AI.processor import get_reader
        reader = get_reader()

        return {
            "status": "AI initialized successfully",
            "easyocr": "OK"
        }

    except Exception as e:
        return {
            "status": "AI initialization failed",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
@app.post("/analyze")
async def analyze(
    document: UploadFile = File(...),
    face: UploadFile = File(None)
):
    import traceback

    document_path = "uploaded_document.png"
    with open(document_path, "wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    face_path = None
    if face is not None:
        face_path = "uploaded_face.png"
        with open(face_path, "wb") as buffer:
            shutil.copyfileobj(face.file, buffer)

    try:
        from AI.processor import analyze_document

        result = analyze_document(document_path, face_path)

        scan_id = save_scan_result(result)
        result["scan_id"] = scan_id

        return result

    except Exception as e:
        return {
            "status": "ANALYZE FAILED",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

    finally:
        if os.path.exists(document_path):
            os.remove(document_path)

        if face_path is not None and os.path.exists(face_path):
            os.remove(face_path)

@app.get("/history")
def history():
    return get_scan_history()
