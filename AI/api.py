from fastapi import FastAPI, UploadFile, File
import shutil
import os

from AI.processor import analyze_document


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="SIH26188 Document Verification API",
    description="AI document processing API for SIH prototype",
    version="1.0"
)


# ==========================================
# HOME / TEST ROUTE
# ==========================================

@app.get("/")
def home():

    return {
        "message": "SIH26188 Document Verification API is running"
    }


# ==========================================
# DOCUMENT ANALYSIS ROUTE
# ==========================================

@app.post("/analyze")
async def analyze(
    document: UploadFile = File(...),
    face: UploadFile = File(None)
):

    # ======================================
    # STEP 1: SAVE DOCUMENT
    # ======================================

    document_path = "uploaded_document.png"

    with open(document_path, "wb") as buffer:

        shutil.copyfileobj(
            document.file,
            buffer
        )


    # ======================================
    # STEP 2: SAVE SECOND FACE IMAGE
    # ======================================

    face_path = None

    if face is not None:

        face_path = "uploaded_face.jpg"

        with open(face_path, "wb") as buffer:

            shutil.copyfileobj(
                face.file,
                buffer
            )


    # ======================================
    # STEP 3: RUN AI PIPELINE
    # ======================================

    try:

        result = analyze_document(
            document_path,
            face_path
        )

    finally:

        # ==================================
        # DELETE DOCUMENT
        # ==================================

        if os.path.exists(document_path):

            os.remove(document_path)


        # ==================================
        # DELETE FACE IMAGE
        # ==================================

        if face_path is not None:

            if os.path.exists(face_path):

                os.remove(face_path)


    # ======================================
    # STEP 4: RETURN RESULT
    # ======================================

    return results 