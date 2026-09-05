import easyocr


# Create the OCR reader
reader = easyocr.Reader(['en'])


# Location of our sample image
image_path = "sample.png"


# Read text from the image
results = reader.readtext(image_path)


# Print the results
print("========== OCR RESULT ==========")

for result in results:

    text = result[1]
    confidence = result[2]

    print("Text:", text)
    print(
        "Confidence:",
        round(confidence * 100, 2),
        "%"
    )

    print("--------------------------------")