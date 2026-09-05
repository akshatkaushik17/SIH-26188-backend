# ==========================================================
# COMBINED RISK SCORE
# ==========================================================


def calculate_ocr_risk(ocr_confidence):
    """
    Convert OCR confidence into a risk score.

    Higher OCR confidence = lower risk.
    Lower OCR confidence = higher risk.

    Returns:
        risk from 0 to 100
    """

    if ocr_confidence >= 90:

        return 0

    elif ocr_confidence >= 80:

        return 10

    elif ocr_confidence >= 70:

        return 25

    elif ocr_confidence >= 50:

        return 50

    else:

        return 80


# ==========================================================
# VALIDATION RISK
# ==========================================================

def calculate_validation_risk(verification):
    """
    Extract the document-validation risk.

    The existing verify_document.py already calculates
    a risk score based on missing document information
    and basic validation checks.

    Returns:
        risk from 0 to 100
    """

    risk = verification.get(
        "risk_score",
        0
    )

    return max(
        0,
        min(
            100,
            float(risk)
        )
    )


# ==========================================================
# TAMPERING RISK
# ==========================================================

def calculate_tampering_risk(tampering):
    """
    Convert tampering detection result into a risk score.

    If tampering is detected, the tampering confidence
    contributes directly to the risk.

    Returns:
        risk from 0 to 100
    """

    tampering_detected = tampering.get(
        "tampering_detected",
        False
    )

    confidence = tampering.get(
        "confidence",
        0
    )


    if tampering_detected:

        return max(
            50,
            min(
                100,
                float(confidence) * 100
            )
        )


    return 0


# ==========================================================
# FACE VERIFICATION RISK
# ==========================================================

def calculate_face_risk(face_verification):
    """
    Convert face verification into a risk score.

    Missing face or face mismatch = high risk.

    Matching face = low risk.

    Returns:
        risk from 0 to 100
    """

    passport_face_detected = (
        face_verification.get(
            "passport_face_detected",
            False
        )
    )

    second_face_detected = (
        face_verification.get(
            "second_face_detected",
            False
        )
    )

    match = face_verification.get(
        "match",
        False
    )


    # ------------------------------------------------------
    # No passport face
    # ------------------------------------------------------

    if not passport_face_detected:

        return 100


    # ------------------------------------------------------
    # No second face
    # ------------------------------------------------------

    if not second_face_detected:

        return 100


    # ------------------------------------------------------
    # Faces do not match
    # ------------------------------------------------------

    if not match:

        return 100


    # ------------------------------------------------------
    # Faces match
    # ------------------------------------------------------

    similarity = face_verification.get(
        "similarity",
        0
    )


    # Convert similarity into a small residual risk.
    #
    # Example:
    #
    # similarity = 0.98
    # face risk = 2
    #
    # similarity = 0.90
    # face risk = 10

    risk = (
        1 - float(similarity)
    ) * 100


    return max(
        0,
        min(
            30,
            risk
        )
    )


# ==========================================================
# FINAL COMBINED RISK SCORE
# ==========================================================

def calculate_risk_score(
    ocr_confidence,
    verification,
    tampering,
    face_verification
):
    """
    Combine all major AI signals into one final risk score.

    Components:

        OCR                = 20%
        Document validation = 25%
        Tampering           = 30%
        Face verification   = 25%

    Returns a dictionary containing:

        final risk score
        risk level
        individual component scores
        explanation
    """


    # ======================================================
    # CALCULATE INDIVIDUAL RISKS
    # ======================================================

    ocr_risk = calculate_ocr_risk(
        ocr_confidence
    )


    validation_risk = calculate_validation_risk(
        verification
    )


    tampering_risk = calculate_tampering_risk(
        tampering
    )


    face_risk = calculate_face_risk(
        face_verification
    )


    # ======================================================
    # WEIGHTED SCORE
    # ======================================================

    final_score = (

        ocr_risk * 0.20

        +

        validation_risk * 0.25

        +

        tampering_risk * 0.30

        +

        face_risk * 0.25
    )


    # Make sure score stays between 0 and 100.

    final_score = max(
        0,
        min(
            100,
            final_score
        )
    )


    final_score = round(
        final_score,
        2
    )


    # ======================================================
    # DETERMINE RISK LEVEL
    # ======================================================

    if final_score < 30:

        risk_level = "LOW"

    elif final_score < 60:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"


    # ======================================================
    # CREATE EXPLANATION
    # ======================================================

    reasons = []


    if ocr_risk >= 50:

        reasons.append(
            "OCR confidence is low."
        )


    if validation_risk >= 50:

        reasons.append(
            "Document validation found significant issues."
        )


    if tampering_risk >= 50:

        reasons.append(
            "Possible document tampering was detected."
        )


    if face_risk >= 50:

        reasons.append(
            "Face verification failed or a required face "
            "could not be detected."
        )


    if not reasons:

        reasons.append(
            "No major risk signals were detected."
        )


    # ======================================================
    # FINAL RESULT
    # ======================================================

    return {

        "risk_score": final_score,

        "risk_level": risk_level,

        "components": {

            "ocr_risk": round(
                ocr_risk,
                2
            ),

            "validation_risk": round(
                validation_risk,
                2
            ),

            "tampering_risk": round(
                tampering_risk,
                2
            ),

            "face_risk": round(
                face_risk,
                2
            )
        },

        "weights": {

            "ocr": 0.20,

            "validation": 0.25,

            "tampering": 0.30,

            "face_verification": 0.25
        },

        "reasons": reasons
    }