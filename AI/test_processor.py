from AI.processor import analyze_document


# ==========================================================
# TEST IMAGES
# ==========================================================

document_image = "rahul.jpg"

second_face_image = "rahul3.jpg"


# ==========================================================
# RUN COMPLETE ANALYSIS
# ==========================================================

result = analyze_document(
    document_image,
    second_face_image
)


# ==========================================================
# DISPLAY FINAL RESULT
# ==========================================================

print()
print("========================================")
print("       FINAL SYSTEM RESULT")
print("========================================")
print()

print(
    "OCR confidence:",
    result["ocr_confidence"]
)

print()

print(
    "Passport number:",
    result["information"].get(
        "passport_number"
    )
)

print(
    "Name:",
    result["information"].get(
        "name"
    )
)

print()

print(
    "Tampering detected:",
    result["tampering"].get(
        "tampering_detected"
    )
)

print()

print(
    "Face match:",
    result["face_verification"].get(
        "match"
    )
)

print(
    "Face similarity:",
    result["face_verification"].get(
        "similarity"
    )
)

print()

print(
    "Risk score:",
    result["risk"]["risk_score"]
)

print(
    "Risk level:",
    result["risk"]["risk_level"]
)

print()

print(
    "Risk reasons:"
)

for reason in result["risk"]["reasons"]:

    print(
        "-",
        reason
    )

print()