import os
import gc

CLOUD_DEPLOYMENT = os.getenv("CLOUD_DEPLOYMENT", "").lower() == "true"
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import torch.nn.functional as F


# Keep CPU usage predictable on small cloud instances.
torch.set_num_threads(1)


def get_model_path():
    return os.path.join(
        os.path.dirname(__file__),
        "models",
        "20180402-114759-vggface2.pt"
    )


def load_face_detector():
    print("Loading lightweight MTCNN face detector...")

    mtcnn = MTCNN(
        image_size=160,
        margin=20,
        keep_all=False,
        device=torch.device("cpu")
    )

    print("MTCNN loaded successfully.")
    return mtcnn


def load_facenet():
    model_path = get_model_path()

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"FaceNet model not found: {model_path}"
        )

    print("Loading FaceNet model...")

    resnet = InceptionResnetV1(
        pretrained=None
    )

    state_dict = torch.load(
        model_path,
        map_location=torch.device("cpu")
    )

    resnet.load_state_dict(state_dict, strict=False)

    del state_dict
    gc.collect()

    resnet.eval()

    print("FaceNet model loaded successfully.")

    return resnet


def load_image(image_path):
    return Image.open(image_path).convert("RGB")


def extract_face(image_path, mtcnn):
    image = load_image(image_path)

    try:
        face = mtcnn(image)
    finally:
        image.close()

    return face


def create_embedding(face, resnet):
    if face is None:
        return None

    face = face.unsqueeze(0)

    with torch.no_grad():
        embedding = resnet(face)

    embedding = F.normalize(
        embedding,
        p=2,
        dim=1
    )

    return embedding


def compare_faces(passport_embedding, second_embedding):
    if passport_embedding is None or second_embedding is None:
        return 0.0

    similarity = F.cosine_similarity(
        passport_embedding,
        second_embedding
    ).item()

    return similarity


def verify_faces(passport_image_path, second_image_path):

    print("Running face verification...")

    # ---------------------------------------------------------
    # STEP 1: Detect faces using MTCNN
    # ---------------------------------------------------------

    mtcnn = load_face_detector()

    passport_face = extract_face(
        passport_image_path,
        mtcnn
    )

    second_face = extract_face(
        second_image_path,
        mtcnn
    )

    passport_detected = passport_face is not None
    second_detected = second_face is not None

    # MTCNN is no longer needed after face extraction.
    del mtcnn
    gc.collect()

    print(
        f"Face detection complete. "
        f"Passport={passport_detected}, "
        f"Second={second_detected}"
    )

    if passport_face is None or second_face is None:
        return {
            "passport_face_detected": passport_detected,
            "second_face_detected": second_detected,
            "similarity": 0.0,
            "threshold": 0.60,
            "match": False,
            "details": (
                "Could not detect a face in one or both images."
            )
        }
    # ---------------------------------------------------------
    # STEP 2: Cloud-safe mode
    # ---------------------------------------------------------

    if CLOUD_DEPLOYMENT:
        print(
            "Cloud deployment detected. "
            "Skipping FaceNet model loading."
        )

        del passport_face
        del second_face
        gc.collect()

        return {
            "passport_face_detected": passport_detected,
            "second_face_detected": second_detected,
            "similarity": 0.0,
            "threshold": 0.60,
            "match": False,
            "details": (
                "Cloud deployment: FaceNet verification skipped "
                "to conserve server resources."
            )
        }

    # ---------------------------------------------------------
    # STEP 3: Load FaceNet only after MTCNN is released
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 2: Load FaceNet only after MTCNN is released
    # ---------------------------------------------------------

    resnet = load_facenet()

    passport_embedding = create_embedding(
        passport_face,
        resnet
    )

    # Release first face tensor as soon as possible.
    del passport_face
    gc.collect()

    second_embedding = create_embedding(
        second_face,
        resnet
    )

    del second_face
    gc.collect()

    # FaceNet is no longer needed after embeddings are created.
    del resnet
    gc.collect()

    # ---------------------------------------------------------
    # STEP 3: Compare embeddings
    # ---------------------------------------------------------

    if passport_embedding is None or second_embedding is None:
        return {
            "passport_face_detected": passport_detected,
            "second_face_detected": second_detected,
            "similarity": 0.0,
            "threshold": 0.60,
            "match": False,
            "details": (
                "Could not generate face embeddings."
            )
        }

    similarity = compare_faces(
        passport_embedding,
        second_embedding
    )

    # Release embeddings after comparison.
    del passport_embedding
    del second_embedding
    gc.collect()

    threshold = 0.60
    match = similarity >= threshold

    print(
        f"Face comparison complete. "
        f"Similarity={similarity:.4f}, "
        f"Match={match}"
    )

    return {
        "passport_face_detected": True,
        "second_face_detected": True,
        "similarity": round(similarity, 4),
        "threshold": threshold,
        "match": match,
        "details": (
            "Faces match."
            if match
            else "Faces do not match."
        )
    }
