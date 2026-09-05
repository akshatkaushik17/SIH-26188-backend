import cv2
import numpy as np
import os


# ==========================================================
# IMAGE LOADING
# ==========================================================

def load_image(image_path):
    """
    Load an image from the given path.

    Returns:
        image = OpenCV image
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    return image


# ==========================================================
# METADATA CHECK
# ==========================================================

def check_metadata(image_path):
    """
    Perform a basic file-level check.

    This checks whether the file exists and
    whether it has a reasonable image format.

    NOTE:
    OpenCV does not provide reliable EXIF metadata
    analysis, so this is intentionally only a basic
    signal.
    """

    reasons = []

    # ------------------------------------------------------
    # Check whether file exists
    # ------------------------------------------------------

    if not os.path.exists(image_path):

        reasons.append(
            "Image file does not exist."
        )

        return {
            "suspicious": True,
            "confidence": 1.0,
            "reasons": reasons
        }


    # ------------------------------------------------------
    # Check file size
    # ------------------------------------------------------

    file_size = os.path.getsize(
        image_path
    )

    if file_size < 5000:

        reasons.append(
            "Image file is unusually small."
        )

        return {
            "suspicious": True,
            "confidence": 0.70,
            "reasons": reasons
        }


    return {
        "suspicious": False,
        "confidence": 0.0,
        "reasons": []
    }


# ==========================================================
# BLUR CHECK
# ==========================================================

def check_blur(image):
    """
    Check whether the image is extremely blurry.

    A very blurry image can make forensic analysis
    unreliable.

    This does NOT mean that a blurry document is fake.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    variance = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


    # Very low variance means the image
    # contains very little sharp detail.

    if variance < 50:

        return {
            "suspicious": True,
            "confidence": 0.20,
            "value": variance,
            "reason":
                "Image is extremely blurry; "
                "tampering analysis may be unreliable."
        }


    return {
        "suspicious": False,
        "confidence": 0.0,
        "value": variance,
        "reason": None
    }


# ==========================================================
# JPEG / COMPRESSION ANALYSIS
# ==========================================================

def check_compression(image):
    """
    Look for unusual local compression differences.

    The image is divided into blocks and the variance
    of the Laplacian is calculated for each block.

    Large differences between neighboring regions can
    indicate that different parts of an image have been
    processed differently.

    IMPORTANT:
    This is only a forensic signal.
    It is NOT proof of tampering.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    height, width = gray.shape

    block_size = 64

    block_values = []


    # ------------------------------------------------------
    # Divide image into blocks
    # ------------------------------------------------------

    for y in range(
        0,
        height - block_size + 1,
        block_size
    ):

        for x in range(
            0,
            width - block_size + 1,
            block_size
        ):

            block = gray[
                y:y + block_size,
                x:x + block_size
            ]

            value = cv2.Laplacian(
                block,
                cv2.CV_64F
            ).var()

            block_values.append(
                value
            )


    # If the image is too small,
    # don't make a decision.

    if len(block_values) < 4:

        return {
            "suspicious": False,
            "confidence": 0.0,
            "variation": 0.0,
            "reason": None
        }


    values = np.array(
        block_values,
        dtype=np.float64
    )


    # ------------------------------------------------------
    # Calculate variation
    # ------------------------------------------------------

    mean_value = np.mean(values)

    standard_deviation = np.std(values)


    if mean_value == 0:

        variation = 0

    else:

        variation = (
            standard_deviation
            /
            mean_value
        )


    # ------------------------------------------------------
    # Determine whether variation is unusually high
    # ------------------------------------------------------

    if variation > 1.5:

        confidence = min(
            0.75,
            variation / 3
        )

        return {
            "suspicious": True,
            "confidence": round(
                confidence,
                3
            ),
            "variation": round(
                variation,
                3
            ),
            "reason":
                "Large local image-quality differences "
                "were detected."
        }


    return {
        "suspicious": False,
        "confidence": 0.0,
        "variation": round(
            variation,
            3
        ),
        "reason": None
    }


# ==========================================================
# EDGE ANALYSIS
# ==========================================================

def check_edges(image):
    """
    Analyse the distribution of edges.

    A document containing unusually sharp local
    boundaries can sometimes indicate pasted or
    manipulated regions.

    Again, this is only a supporting signal.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_ratio = (
        np.count_nonzero(edges)
        /
        edges.size
    )


    # Extremely high edge density can indicate
    # a noisy or heavily processed image.

    if edge_ratio > 0.35:

        return {
            "suspicious": True,
            "confidence": 0.25,
            "edge_ratio": round(
                edge_ratio,
                4
            ),
            "reason":
                "Unusually high edge density detected."
        }


    return {
        "suspicious": False,
        "confidence": 0.0,
        "edge_ratio": round(
            edge_ratio,
            4
        ),
        "reason": None
    }


# ==========================================================
# NOISE ANALYSIS
# ==========================================================

def check_noise(image):
    """
    Analyse local noise variation.

    A sudden difference in noise characteristics
    between regions can sometimes occur after
    image editing.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Estimate high-frequency noise.
    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    noise = cv2.absdiff(
        gray,
        blurred
    )

    noise_mean = np.mean(
        noise
    )

    noise_std = np.std(
        noise
    )


    # Very unusual noise level.
    if noise_mean > 30:

        return {
            "suspicious": True,
            "confidence": 0.20,
            "noise_mean": round(
                float(noise_mean),
                3
            ),
            "noise_std": round(
                float(noise_std),
                3
            ),
            "reason":
                "Unusually high image noise detected."
        }


    return {
        "suspicious": False,
        "confidence": 0.0,
        "noise_mean": round(
            float(noise_mean),
            3
        ),
        "noise_std": round(
            float(noise_std),
            3
        ),
        "reason": None
    }


# ==========================================================
# MAIN TAMPERING DETECTION FUNCTION
# ==========================================================

def detect_tampering(image_path):
    """
    Perform multi-signal tampering analysis.

    Returns:

        tampering_detected
        confidence
        reasons
        details
    """

    # ------------------------------------------------------
    # Load image
    # ------------------------------------------------------

    image = load_image(
        image_path
    )


    # ------------------------------------------------------
    # Run individual checks
    # ------------------------------------------------------

    metadata_result = check_metadata(
        image_path
    )

    blur_result = check_blur(
        image
    )

    compression_result = check_compression(
        image
    )

    edge_result = check_edges(
        image
    )

    noise_result = check_noise(
        image
    )


    # ------------------------------------------------------
    # Collect suspicious signals
    # ------------------------------------------------------

    suspicious_results = [

        metadata_result,

        blur_result,

        compression_result,

        edge_result,

        noise_result
    ]


    reasons = []

    confidence_values = []


    for result in suspicious_results:

        if result.get("suspicious"):

            reason = result.get(
                "reason"
            )

            if reason:

                reasons.append(
                    reason
                )

            confidence_values.append(
                result.get(
                    "confidence",
                    0
                )
            )


    # ------------------------------------------------------
    # Calculate combined confidence
    # ------------------------------------------------------

    if confidence_values:

        # Average of suspicious signals.
        confidence = sum(
            confidence_values
        ) / len(
            confidence_values
        )

    else:

        confidence = 0.0


    # ------------------------------------------------------
    # Determine final decision
    # ------------------------------------------------------

    # We require more than a tiny signal before
    # declaring potential tampering.

    tampering_detected = (
        confidence >= 0.50
        or
        len(reasons) >= 2
    )


    # ------------------------------------------------------
    # If nothing suspicious was found
    # ------------------------------------------------------

    if not reasons:

        reasons.append(
            "No significant image-level tampering "
            "signals were detected."
        )


    # ------------------------------------------------------
    # Create detailed result
    # ------------------------------------------------------

    details = {

        "metadata": metadata_result,

        "blur": blur_result,

        "compression": compression_result,

        "edges": edge_result,

        "noise": noise_result
    }


    # ------------------------------------------------------
    # Final result
    # ------------------------------------------------------

    return {

        "tampering_detected":
            bool(tampering_detected),

        "confidence": round(
            float(confidence),
            3
        ),

        "reasons": reasons,

        "details": details
    }


# ==========================================================
# DIRECT TEST
# ==========================================================

if __name__ == "__main__":

    # Change this only if your sample image
    # has a different filename.

    image_path = "sample.png"


    print()
    print(
        "========================================"
    )

    print(
        "       TAMPERING DETECTION TEST"
    )

    print(
        "========================================"
    )

    print()


    result = detect_tampering(
        image_path
    )


    print(
        "Tampering detected:",
        result["tampering_detected"]
    )

    print(
        "Confidence:",
        result["confidence"]
    )

    print()


    print(
        "Reasons:"
    )

    for reason in result["reasons"]:

        print(
            "-",
            reason
        )


    print()

    print(
        "Detailed analysis:"
    )

    for key, value in result[
        "details"
    ].items():

        print(
            key,
            ":",
            value
        )

    print()