from PIL import Image
from facenet_pytorch import MTCNN


# ==========================================
# CREATE FACE DETECTOR
# ==========================================

print()
print("========================================")
print("       FACE DETECTION TEST")
print("========================================")
print()

print("Loading face detection model...")

mtcnn = MTCNN(
    image_size=160,
    margin=20,
    keep_all=True
)

print("Face detection model loaded!")
print()


# ==========================================
# LOAD IMAGE
# ==========================================

image_path = "sample.png"

print("Loading image:")
print(image_path)
print()

image = Image.open(
    image_path
).convert("RGB")


# ==========================================
# DETECT FACES
# ==========================================

print("Searching for faces...")

boxes, probabilities = mtcnn.detect(
    image
)


# ==========================================
# DISPLAY RESULT
# ==========================================

if boxes is None:

    print()
    print("No face detected.")

else:

    print()
    print(
        "Number of faces detected:",
        len(boxes)
    )

    print()

    for i, probability in enumerate(
        probabilities
    ):

        print(
            "Face",
            i + 1,
            "confidence:",
            round(
                float(probability),
                4
            )
        )


print()
print("========================================")
print("             TEST COMPLETE")
print("========================================")