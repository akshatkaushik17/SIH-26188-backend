import cv2


def preprocess_image(input_path, output_path):
    """
    Prepare the document image for OCR.
    This version uses gentle preprocessing
    so that letters are not damaged.
    """

    # -----------------------------------------
    # STEP 1: Read the original image
    # -----------------------------------------

    image = cv2.imread(input_path)

    if image is None:
        raise FileNotFoundError(
            "Could not find the image."
        )


    # -----------------------------------------
    # STEP 2: Make the image larger
    # -----------------------------------------

    image = cv2.resize(
        image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )


    # -----------------------------------------
    # STEP 3: Convert to grayscale
    # -----------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )


    # -----------------------------------------
    # STEP 4: Improve contrast gently
    # -----------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)


    # -----------------------------------------
    # STEP 5: Save processed image
    # -----------------------------------------

    success = cv2.imwrite(
        output_path,
        enhanced
    )

    if not success:
        raise Exception(
            "Could not save processed image."
        )


    print("Image preprocessing completed.")
    print("Saved processed image to:")
    print(output_path)