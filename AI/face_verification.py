from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import torch.nn.functional as F

# Models are loaded only when face verification is actually used.
mtcnn = None
resnet = None


def get_face_models():
    global mtcnn, resnet

    if mtcnn is None or resnet is None:
        print("Loading face recognition model...")

        mtcnn = MTCNN(
            image_size=160,
            margin=20,
            keep_all=False
        )

        resnet = InceptionResnetV1(
            pretrained="vggface2"
        ).eval()

        print("Face recognition model loaded.")

    return mtcnn, resnet


def load_image(image_path):
    return Image.open(image_path).convert("RGB")


def extract_face(image_path):
    mtcnn, _ = get_face_models()

    image = load_image(image_path)
    face = mtcnn(image)

    return face


def create_embedding(face):
    _, resnet = get_face_models()

    if face is None:
        return None

    face = face.unsqueeze(0)

    with torch.no_grad():
        embedding = resnet(face)

    embedding = F.normalize(embedding, p=2, dim=1)

    return embedding


def compare_faces(passport_face, second_face):
    if passport_face is None or second_face is None:
        return 0.0

    similarity = F.cosine_similarity(
        passport_face,
        second_face
    ).item()

    return similarity


def verify_faces(passport_image_path, second_image_path):
    passport_face = extract_face(passport_image_path)
    second_face = extract_face(second_image_path)

    passport_embedding = create_embedding(passport_face)
    second_embedding = create_embedding(second_face)

    if passport_embedding is None or second_embedding is None:
        return {
            "passport_face_detected": passport_face is not None,
            "second_face_detected": second_face is not None,
            "similarity": 0.0,
            "threshold": 0.60,
            "match": False,
            "details": "Could not detect a face in one or both images."
        }

    similarity = compare_faces(
        passport_embedding,
        second_embedding
    )

    threshold = 0.60
    match = similarity >= threshold

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
