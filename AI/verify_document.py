def verify_document(information, average_confidence):
    """
    Perform basic document verification.

    This does NOT prove that a document is genuine.
    It only checks simple signals such as:
    - missing information
    - OCR confidence
    """

    # ==========================================
    # START WITH ZERO RISK
    # ==========================================

    risk_score = 0

    warnings = []


    # ==========================================
    # CHECK 1: NAME
    # ==========================================

    if not information.get("name"):

        risk_score += 25

        warnings.append(
            "Name could not be detected."
        )


    # ==========================================
    # CHECK 2: DATE OF BIRTH
    # ==========================================

    if not information.get("date_of_birth"):

        risk_score += 25

        warnings.append(
            "Date of birth could not be detected."
        )


    # ==========================================
    # CHECK 3: DOCUMENT NUMBER
    # ==========================================

    if not information.get("document_number"):

        risk_score += 25

        warnings.append(
            "Document number could not be detected."
        )


    # ==========================================
    # CHECK 4: NATIONALITY
    # ==========================================

    if not information.get("nationality"):

        risk_score += 10

        warnings.append(
            "Nationality could not be detected."
        )


    # ==========================================
    # CHECK 5: OCR CONFIDENCE
    # ==========================================

    if average_confidence < 50:

        risk_score += 15

        warnings.append(
            "OCR confidence is very low."
        )

    elif average_confidence < 75:

        risk_score += 8

        warnings.append(
            "OCR confidence is relatively low."
        )


    # ==========================================
    # MAKE SURE SCORE DOES NOT EXCEED 100
    # ==========================================

    if risk_score > 100:

        risk_score = 100


    # ==========================================
    # DETERMINE STATUS
    # ==========================================

    if risk_score < 30:

        status = "PASS"

    else:

        status = "REVIEW"


    # ==========================================
    # IF NO WARNINGS EXIST
    # ==========================================

    if len(warnings) == 0:

        warnings.append(
            "No obvious issues detected."
        )


    # ==========================================
    # FINAL RESULT
    # ==========================================

    result = {

        "status": status,

        "risk_score": risk_score,

        "average_ocr_confidence": round(
            average_confidence,
            2
        ),

        "warnings": warnings
    }


    return result