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
@app.get("/test-easyocr-reader")
def test_easyocr_reader():
    try:
        import os
        import easyocr
        from PIL import Image, ImageDraw

        model_dir = os.path.join(
            os.path.dirname(__file__),
            "models"
        )

        test_image = "/tmp/easyocr_test.png"

        img = Image.new("RGB", (800, 200), "white")
        draw = ImageDraw.Draw(img)
        draw.text((50, 70), "HELLO WORLD 12345", fill="black")
        img.save(test_image)

        reader = easyocr.Reader(
            ['en'],
            model_storage_directory=model_dir,
            download_enabled=False,
            gpu=False,
            verbose=False,
            detector=False
        )

        result = reader.recognize(
    test_image,
    horizontal_list=[[0, 800, 70, 130]],
    free_list=[]
)

        return {
            "status": "EasyOCR recognition test OK",
            "reader_loaded": reader is not None,
            "result": str(result)
        }

    except Exception as e:
        import traceback

        return {
            "status": "EasyOCR recognition test FAILED",
            "error": str(e),
            "traceback": traceback.format_exc()
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
@app.get("/test-tesseract")
def test_tesseract():
    import shutil

    tesseract_path = shutil.which("tesseract")

    return {
        "tesseract_available": tesseract_path is not None,
        "path": tesseract_path
    }
@app.get("/test-easyocr-reader")
@app.get("/test-ai")
def test_ai():
    try:
        from .processor import get_reader

        reader = get_reader()

        return {
            "status": "AI OK",
            "reader_loaded": reader is not None
        }

    except Exception as e:
        import traceback

        return {
            "status": "AI FAILED",
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
@app.get("/test-easyocr-full")
def test_easyocr_full():
    try:
        import os
        import easyocr

        model_dir = os.path.join(os.path.dirname(__file__), "models")

        reader = easyocr.Reader(
            ['en'],
            model_storage_directory=model_dir,
            download_enabled=False,
            gpu=False,
            verbose=False
        )

        return {
            "status": "FULL EASYOCR OK",
            "reader_loaded": reader is not None
        }

    except Exception as e:
        import traceback
        return {
            "status": "FULL EASYOCR FAILED",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
