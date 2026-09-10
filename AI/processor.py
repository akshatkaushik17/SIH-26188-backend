import os
import easyocr

from AI.extract_data import extract_information
from AI.preprocess import preprocess_image
from AI.verify_document import verify_document
from AI.tampering import detect_tampering
from AI.face_verification import verify_faces
from AI.risk_score import calculate_risk_score


# ==========================================================
# OCR READER
# ==========================================================

reader = None


def get_reader():
    global reader

    if reader is None:
        print("Initializing EasyOCR from bundled models...")

        model_dir = os.path.join(
            os.path.dirname(__file__),
            "models"
        )

        reader = easyocr.Reader(
    ['en'],
    model_storage_directory=model_dir,
    gpu=False
)

    return reader


# ==========================================================
# MAIN DOCUMENT ANALYSIS FUNCTION
# ==========================================================

def analyze_document(
    image_path,
    face_image_path=None
):

    print()
    print("========================================")
    print("       STARTING DOCUMENT ANALYSIS")
    print("========================================")
    print()


    # ======================================================
    # STEP 1: PREPROCESS IMAGE
    # ======================================================

    print(
        "Step 1: Improving image quality..."
    )

    processed_image = "processed_sample.png"

    preprocess_image(
        image_path,
        processed_image
    )


    # ======================================================
    # STEP 2: RUN OCR
    # ======================================================

    print()
    print(
        "Step 2: Reading text with OCR..."
    )

    results = get_reader().readtext(
    processed_image
)


    # ======================================================
    # STEP 3: COMBINE OCR TEXT
    # ======================================================

    print()
    print(
        "Step 3: Combining detected text..."
    )

    full_text = ""

    total_confidence = 0

    detected_items = 0


    for result in results:

        text = result[1]

        confidence = result[2]

        full_text = (
            full_text
            + text
            + "\n"
        )

        total_confidence += confidence

        detected_items += 1


    # ======================================================
    # STEP 4: CALCULATE OCR CONFIDENCE
    # ======================================================

    if detected_items > 0:

        average_confidence = (
            total_confidence
            / detected_items
        ) * 100

    else:

        average_confidence = 0


    # ======================================================
    # STEP 5: EXTRACT INFORMATION
    # ======================================================

    print()
    print(
        "Step 4: Extracting useful information..."
    )

    information = extract_information(
        full_text
    )


    # ======================================================
    # STEP 6: VERIFY DOCUMENT
    # ======================================================

    print()
    print(
        "Step 5: Checking document..."
    )

    verification = verify_document(
        information,
        average_confidence
    )


    # ======================================================
    # STEP 7: DETECT TAMPERING
    # ======================================================

    print()
    print(
        "Step 6: Checking for possible tampering..."
    )

    # IMPORTANT:
    #
    # Tampering detection uses the ORIGINAL image.
    #
    # OCR uses the processed image.
    #
    # This prevents OCR preprocessing from interfering
    # with the forensic/tampering analysis.

    tampering = detect_tampering(
        image_path
    )


    # ======================================================
    # STEP 8: FACE VERIFICATION
    # ======================================================

    print()
    print(
        "Step 7: Checking face identity..."
    )


    # ------------------------------------------------------
    # DEFAULT RESULT
    # ------------------------------------------------------
    #
    # If no second face image is supplied, we don't try
    # to perform face verification.
    #

    if face_image_path is not None:

        print(
            "Second face image supplied."
        )

        print(
            "Running face verification..."
        )

        face_verification = verify_faces(
            image_path,
            face_image_path
        )

    else:

        print(
            "No second face image supplied."
        )

        print(
            "Face verification skipped."
        )

        face_verification = {

            "passport_face_detected": False,

            "second_face_detected": False,

            "similarity": 0.0,

            "threshold": 0.60,

            "match": False,

            "details":
                "Face verification was not performed "
                "because no second face image was supplied."
        }


    # ======================================================
    # STEP 9: CALCULATE COMBINED RISK SCORE
    # ======================================================

    print()
    print(
        "Step 8: Calculating combined risk score..."
    )


    risk_result = calculate_risk_score(

        ocr_confidence=average_confidence,

        verification=verification,

        tampering=tampering,

        face_verification=face_verification
    )


    # ======================================================
    # STEP 10: CREATE FINAL RESULT
    # ======================================================

    final_result = {

        # --------------------------------------------------
        # RAW OCR
        # --------------------------------------------------

        "raw_text": full_text,


        # --------------------------------------------------
        # OCR
        # --------------------------------------------------

        "ocr_confidence": round(
            average_confidence,
            2
        ),


        # --------------------------------------------------
        # STRUCTURED INFORMATION
        # --------------------------------------------------

        "information": information,


        # --------------------------------------------------
        # DOCUMENT VALIDATION
        # --------------------------------------------------

        "verification": verification,


        # --------------------------------------------------
        # TAMPERING
        # --------------------------------------------------

        "tampering": tampering,


        # --------------------------------------------------
        # FACE VERIFICATION
        # --------------------------------------------------

        "face_verification": face_verification,


        # --------------------------------------------------
        # COMBINED RISK
        # --------------------------------------------------

        "risk": risk_result
    }


    # ======================================================
    # STEP 11: DISPLAY SUMMARY
    # ======================================================

    print()

    print(
        "========================================"
    )

    print(
        "       DOCUMENT ANALYSIS COMPLETED"
    )

    print(
        "========================================"
    )

    print()


    # ------------------------------------------------------
    # OCR
    # ------------------------------------------------------

    print(
        "OCR confidence:",
        round(
            average_confidence,
            2
        ),
        "%"
    )


    # ------------------------------------------------------
    # TAMPERING
    # ------------------------------------------------------

    print()

    print(
        "Tampering detected:",
        tampering[
            "tampering_detected"
        ]
    )

    print(
        "Tampering confidence:",
        tampering[
            "confidence"
        ]
    )


    # ------------------------------------------------------
    # FACE
    # ------------------------------------------------------

    print()

    print(
        "Face match:",
        face_verification[
            "match"
        ]
    )

    print(
        "Face similarity:",
        face_verification[
            "similarity"
        ]
    )


    # ------------------------------------------------------
    # RISK
    # ------------------------------------------------------

    print()

    print(
        "Final risk score:",
        risk_result[
            "risk_score"
        ]
    )

    print(
        "Risk level:",
        risk_result[
            "risk_level"
        ]
    )

    print()


    # ======================================================
    # STEP 12: RETURN RESULT
    # ======================================================

    return final_result
