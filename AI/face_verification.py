from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import torch.nn.functional as F


# ==========================================================
# CREATE FACE DETECTOR
# ==========================================================

mtcnn = MTCNN(
    image_size=160,
    margin=20,
    keep_all=False
)


# ==========================================================
# CREATE FACE RECOGNITION MODEL
# ==========================================================

print("Loading face recognition model...")

resnet = InceptionResnetV1(
    pretrained="vggface2"
).eval()

print("Face recognition model loaded.")


# ==========================================================
# LOAD IMAGE
# ==========================================================

def load_image(image_path):
    """
    Load an image and convert it to RGB.
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    return image


# ==========================================================
# EXTRACT FACE
# ==========================================================

def extract_face(image_path):
    """
    Detect and extract one face from an image.

    Returns:
        face_tensor
        or None if no face is found
    """

    image = load_image(
        image_path
    )

    face = mtcnn(
        image
    )

    return face


# ==========================================================
# CREATE FACE EMBEDDING
# ==========================================================

def create_embedding(face):
    """
    Convert a detected face into a numerical
    face embedding.
    """

    if face is None:

        return None


    # Add batch dimension.
    #
    # Before:
    #
    # [3, 160, 160]
    #
    # After:
    #
    # [1, 3, 160, 160]

    face = face.unsqueeze(0)


    # Generate embedding.

    with torch.no_grad():

        embedding = resnet(
            face
        )


    # Normalize embedding.

    embedding = F.normalize(
        embedding,
        p=2,
        dim=1
    )


    return embedding


# ==========================================================
# COMPARE TWO FACES
# ==========================================================

def compare_faces(
    passport_face,
    second_face
):
    """
    Compare two face embeddings using cosine similarity.
    """

    similarity = F.cosine_similarity(
        passport_face,
        second_face
    )


    return float(
        similarity.item()
    )


# ==========================================================
# MAIN FACE VERIFICATION FUNCTION
# ==========================================================

def verify_faces(
    passport_image_path,
    second_image_path
):
    """
    Complete face verification pipeline.

    1. Detect face in passport.
    2. Detect face in second image.
    3. Generate embeddings.
    4. Compare embeddings.
    5. Return similarity and match result.
    """


    # ======================================================
    # STEP 1: EXTRACT PASSPORT FACE
    # ======================================================

    print()
    print(
        "Step 1: Detecting face in passport..."
    )

    passport_face = extract_face(
        passport_image_path
    )


    if passport_face is None:

        return {

            "passport_face_detected": False,

            "second_face_detected": False,

            "similarity": 0.0,

            "match": False,

            "details":
                "No face could be detected in the passport."
        }


    print(
        "Passport face detected."
    )


    # ======================================================
    # STEP 2: EXTRACT SECOND FACE
    # ======================================================

    print()
    print(
        "Step 2: Detecting face in second image..."
    )

    second_face = extract_face(
        second_image_path
    )


    if second_face is None:

        return {

            "passport_face_detected": True,

            "second_face_detected": False,

            "similarity": 0.0,

            "match": False,

            "details":
                "No face could be detected in the second image."
        }


    print(
        "Second face detected."
    )


    # ======================================================
    # STEP 3: CREATE PASSPORT EMBEDDING
    # ======================================================

    print()
    print(
        "Step 3: Creating passport face embedding..."
    )

    passport_embedding = create_embedding(
        passport_face
    )


    # ======================================================
    # STEP 4: CREATE SECOND FACE EMBEDDING
    # ======================================================

    print(
        "Step 4: Creating second face embedding..."
    )

    second_embedding = create_embedding(
        second_face
    )


    # ======================================================
    # STEP 5: COMPARE FACES
    # ======================================================

    print()
    print(
        "Step 5: Comparing faces..."
    )

    similarity = compare_faces(
        passport_embedding,
        second_embedding
    )


    # ======================================================
    # STEP 6: DETERMINE MATCH
    # ======================================================

    # Initial development threshold.
    #
    # We will NOT blindly treat this as a legally
    # reliable identity threshold.
    #
    # Later we can calibrate this using test images.

    threshold = 0.60


    match = (
        similarity >= threshold
    )


    # ======================================================
    # STEP 7: CREATE EXPLANATION
    # ======================================================

    if match:

        details = (
            "The two detected faces have "
            "sufficient embedding similarity "
            "for a potential identity match."
        )

    else:

        details = (
            "The two detected faces do not "
            "have sufficient embedding similarity "
            "for a match."
        )


    # ======================================================
    # STEP 8: RETURN RESULT
    # ======================================================

    return {

        "passport_face_detected":
            True,

        "second_face_detected":
            True,

        "similarity":
            round(
                similarity,
                4
            ),

        "threshold":
            threshold,

        "match":
            bool(match),

        "details":
            details
    }