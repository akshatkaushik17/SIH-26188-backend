import easyocr

from AI.preprocess import preprocess_image
from AI.extract_data import extract_information


# ==========================================================
# SETTINGS
# ==========================================================

input_image = "sample.png"

processed_image = "processed_extraction_test.png"


# ==========================================================
# CREATE OCR READER
# ==========================================================

print()
print("Starting OCR...")

reader = easyocr.Reader(
    ['en']
)


# ==========================================================
# PREPROCESS IMAGE
# ==========================================================

print()
print("Preprocessing image...")

preprocess_image(
    input_image,
    processed_image
)


# ==========================================================
# RUN OCR
# ==========================================================

print()
print("Reading image...")

results = reader.readtext(
    processed_image
)


# ==========================================================
# COMBINE OCR TEXT
# ==========================================================

full_text = ""

for result in results:

    text = result[1]

    confidence = result[2]

    full_text += text + "\n"

    print(
        "OCR:",
        text,
        "| Confidence:",
        round(confidence, 2)
    )


# ==========================================================
# SHOW RAW OCR
# ==========================================================

print()
print("========== RAW OCR TEXT ==========")
print()

print(full_text)


# ==========================================================
# EXTRACT INFORMATION
# ==========================================================

print()
print("Extracting structured information...")

information = extract_information(
    full_text
)


# ==========================================================
# SHOW STRUCTURED DATA
# ==========================================================

print()
print(
    "========== STRUCTURED PASSPORT DATA =========="
)
print()

for key, value in information.items():

    print(
        key,
        ":",
        value
    )

print()