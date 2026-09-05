from AI.face_verification import verify_faces


# ==========================================================
# TEST IMAGES
# ==========================================================

passport_image = "rahul.jpg"

second_image = "rahul3.jpg"


# ==========================================================
# RUN FACE VERIFICATION
# ==========================================================

print()
print("========================================")
print("       FACE VERIFICATION TEST")
print("========================================")
print()

result = verify_faces(
    passport_image,
    second_image
)


# ==========================================================
# DISPLAY RESULT
# ==========================================================

print()
print("========================================")
print("       FACE VERIFICATION RESULT")
print("========================================")
print()

print(
    "Passport face detected:",
    result["passport_face_detected"]
)

print(
    "Second face detected:",
    result["second_face_detected"]
)

print(
    "Similarity:",
    result["similarity"]
)

print(
    "Threshold:",
    result["threshold"]
)

print(
    "Match:",
    result["match"]
)

print(
    "Details:",
    result["details"]
)

print()