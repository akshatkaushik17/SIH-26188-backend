import os
import cv2
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

        print("Initializing EasyOCR recognizer from bundled models...")

        model_dir = os.path.join(
            os.path.dirname(__file__),
            "models"
        )

        # IMPORTANT:
        # detector=False prevents EasyOCR from loading
        # the large text-detection model.
        #
        # This is required for the memory-limited
        # FastAPI Cloud deployment.

        reader = easyocr.Reader(
            ['en'],
            model_storage_directory=model_dir,
            download_enabled=False,
            gpu=False,
            verbose=False,
            detector=False
        )

        print("EasyOCR recognizer loaded successfully.")

    return reader


# ==========================================================
# LIGHTWEIGHT OCR
# ==========================================================
def run_lightweight_ocr(image_path):
    print("Running memory-efficient OCR...")

    image = cv2.imread(image_path)

    if image is None:
        print("OCR ERROR: image could not be loaded.")
        return "", 0.0

    height, width = image.shape[:2]

    # Limit image size to reduce cloud memory usage.
    max_width = 1200

    if width > max_width:
        scale = max_width / width
        new_width = max_width
        new_height = int(height * scale)

        image = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        print(
            f"OCR image resized from "
            f"{width}x{height} to "
            f"{new_width}x{new_height}"
        )

    ocr_reader = get_reader()

    crop_height = image.shape[0]
    crop_width = image.shape[1]

    temp_file = "ocr_single_region.png"

    cv2.imwrite(temp_file, image)

    try:
        result = ocr_reader.recognize(
            temp_file,
            horizontal_list=[
                [0, crop_width, 0, crop_height]
            ],
            free_list=[]
        )

        all_results = []

        for item in result:
            if len(item) < 3:
                continue

            text = str(item[1]).strip()
            confidence = float(item[2])

            if text:
                all_results.append(
                    (text, confidence)
                )

                print(
                    f"OCR: {text} "
                    f"(confidence={confidence:.3f})"
                )

        if not all_results:
            print("OCR detected no text.")
            return "", 0.0

        useful_results = [
            item
            for item in all_results
            if item[1] >= 0.10
        ]

        if not useful_results:
            useful_results = all_results

        full_text = ""

        total_confidence = 0.0

        for text, confidence in useful_results:
            full_text += text + "\n"
            total_confidence += confidence

        average_confidence = (
            total_confidence /
            len(useful_results)
        ) * 100

        print("OCR completed.")
        print(
            "Detected OCR items:",
            len(useful_results)
        )

        print(
            "OCR confidence:",
            round(average_confidence, 2),
            "%"
        )

        return full_text, average_confidence

    except Exception as e:
        print("OCR failed:", str(e))
        return "", 0.0

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
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

    full_text, average_confidence = run_lightweight_ocr(
        processed_image
    )

    # ======================================================
    # STEP 3: EXTRACT INFORMATION
    # ======================================================

    print()
    print(
        "Step 3: Extracting useful information..."
    )

    information = extract_information(
        full_text
    )

    # ======================================================
    # STEP 4: VERIFY DOCUMENT
    # ======================================================

    print()
    print(
        "Step 4: Checking document..."
    )

    verification = verify_document(
        information,
        average_confidence
    )

    # ======================================================
    # STEP 5: DETECT TAMPERING
    # ======================================================

    print()
    print(
        "Step 5: Checking for possible tampering..."
    )

    # IMPORTANT:
    #
    # Tampering detection uses ORIGINAL image.
    #
    # OCR uses processed image.
    #
    # This keeps OCR preprocessing separate from
    # forensic/tampering analysis.

    tampering = detect_tampering(
        image_path
    )
    # ======================================================
    # STEP 6: VERIFY FACE IDENTITY
    # ======================================================

    print()
    print(
        "Step 6: Checking face identity..."
    )

    if face_image_path:
        print("Second face image supplied.")

        try:
            face_verification = verify_faces(
                image_path,
                face_image_path
            )

        except Exception as e:
            print(
                "Face verification failed:",
                str(e)
            )

            face_verification = {
                "passport_face_detected": False,
                "second_face_detected": False,
                "similarity": 0.0,
                "threshold": 0.60,
                "match": False,
                "details": (
                    f"Face verification failed: {str(e)}"
                )
            }

    else:
        print("No second face image supplied.")

        face_verification = {
            "passport_face_detected": False,
            "second_face_detected": False,
            "similarity": 0.0,
            "threshold": 0.60,
            "match": False,
            "details": "No second face image supplied."
        }

    # ======================================================
    # STEP 7: CALCULATE COMBINED RISK SCORE
    # ======================================================
    # STEP 7: CALCULATE COMBINED RISK SCORE
    # ======================================================

    print()
    print(
        "Step 7: Calculating combined risk score..."
    )

    risk_result = calculate_risk_score(

        ocr_confidence=average_confidence,

        verification=verification,

        tampering=tampering,

        face_verification=face_verification
    )

    # ======================================================
    # STEP 8: CREATE FINAL RESULT
    # ======================================================

    final_result = {

        "raw_text": full_text,

        "ocr_confidence": round(
            average_confidence,
            2
        ),

        "information": information,

        "verification": verification,

        "tampering": tampering,

        "face_verification": face_verification,

        "risk": risk_result
    }

    # ======================================================
    # STEP 9: DISPLAY SUMMARY
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

    print(
        "OCR confidence:",
        round(
            average_confidence,
            2
        ),
        "%"
    )

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
    # STEP 10: RETURN RESULT
    # ======================================================

    return final_result
