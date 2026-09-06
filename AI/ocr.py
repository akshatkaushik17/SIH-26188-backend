import easyocr
import cv2


# Create OCR reader once when the backend starts
reader = easyocr.Reader(
    ['en'],
    gpu=False
)


def read_text(image_path):
    """
    Read text from a document image.

    Returns:
        raw_text: Combined OCR text
        average_confidence: Average OCR confidence (0-100)
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Increase local contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    processed_image = clahe.apply(gray)

    # Light sharpening
    kernel = cv2.GaussianBlur(
        processed_image,
        (0, 0),
        3
    )

    processed_image = cv2.addWeighted(
        processed_image,
        1.8,
        kernel,
        -0.8,
        0
    )

    # Run OCR
    results = reader.readtext(
        processed_image,
        detail=1,
        paragraph=False,
        mag_ratio=1
    )

    extracted_text = []

    total_confidence = 0

    for result in results:

        text = result[1]
        confidence = result[2]

        extracted_text.append(
            text
        )

        total_confidence += confidence


    # Calculate average confidence
    if results:

        average_confidence = (
            total_confidence / len(results)
        ) * 100

    else:

        average_confidence = 0


    # Combine all detected text
    raw_text = "\n".join(
        extracted_text
    )


    return (
        raw_text,
        round(
            average_confidence,
            2
        )
    )


# Test mode
if __name__ == "__main__":

    raw_text, confidence = read_text(
        "passport_input.png"
    )

    print()
    print(
        "========== OCR RESULT =========="
    )
    print()

    print(
        raw_text
    )

    print()

    print(
        "Average Confidence:",
        confidence,
        "%"
    )
