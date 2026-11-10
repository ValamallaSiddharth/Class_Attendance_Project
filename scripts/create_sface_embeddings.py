import cv2
import os
import pickle
import numpy as np

# ============================================================
# PATHS
# ============================================================

DATASET_DIR = "cropped_dataset"
MODEL_DIR = "models"

YUNET_MODEL = os.path.join(
    MODEL_DIR,
    "face_detection_yunet_2023mar.onnx"
)

SFACE_MODEL = os.path.join(
    MODEL_DIR,
    "face_recognition_sface_2021dec.onnx"
)

OUTPUT_EMBEDDINGS = os.path.join(
    MODEL_DIR,
    "sface_embeddings.pkl"
)

# ============================================================
# CHECK REQUIRED FILES
# ============================================================

if not os.path.exists(DATASET_DIR):
    print("Error: cropped_dataset folder not found.")
    print("Run: python scripts\\crop_dataset_faces.py")
    exit()

if not os.path.exists(YUNET_MODEL):
    print("Error: YuNet model not found.")
    print("Missing:", YUNET_MODEL)
    exit()

if not os.path.exists(SFACE_MODEL):
    print("Error: SFace model not found.")
    print("Missing:", SFACE_MODEL)
    exit()

# ============================================================
# LOAD YUNET + SFACE
# ============================================================

detector = cv2.FaceDetectorYN_create(
    YUNET_MODEL,
    "",
    (320, 320),
    0.6,
    0.3,
    5000
)

recognizer = cv2.FaceRecognizerSF_create(
    SFACE_MODEL,
    ""
)

# ============================================================
# FUNCTIONS
# ============================================================

def detect_largest_face(image):
    height, width = image.shape[:2]

    detector.setInputSize((width, height))

    _, faces = detector.detect(image)

    if faces is None:
        return None

    largest_face = max(
        faces,
        key=lambda face: face[2] * face[3]
    )

    return largest_face


def create_embedding(image, face):
    aligned_face = recognizer.alignCrop(image, face)

    embedding = recognizer.feature(aligned_face)

    embedding = embedding.flatten()

    norm = np.linalg.norm(embedding)

    if norm == 0:
        return None

    embedding = embedding / norm

    return embedding


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

student_embeddings = {}

total_images_used = 0
total_failed = 0

for roll_no in sorted(os.listdir(DATASET_DIR)):

    student_path = os.path.join(DATASET_DIR, roll_no)

    if not os.path.isdir(student_path):
        continue

    print(f"\nProcessing: {roll_no}")

    embeddings = []
    failed_count = 0

    for image_name in os.listdir(student_path):

        if not image_name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(student_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not read: {image_path}")
            failed_count += 1
            continue

        face = detect_largest_face(image)

        if face is None:
            print(f"No face detected by YuNet: {image_path}")
            failed_count += 1
            continue

        embedding = create_embedding(image, face)

        if embedding is None:
            print(f"Embedding failed: {image_path}")
            failed_count += 1
            continue

        embeddings.append(embedding)
        total_images_used += 1

    if len(embeddings) > 0:
        student_embeddings[roll_no] = embeddings

    print(f"Embeddings created for {roll_no}: {len(embeddings)}")
    print(f"Failed images for {roll_no}: {failed_count}")

    total_failed += failed_count

# ============================================================
# SAVE EMBEDDINGS
# ============================================================

if not student_embeddings:
    print("\nWarning: No student embeddings generated from dataset.")
    if os.path.exists(OUTPUT_EMBEDDINGS) and os.path.getsize(OUTPUT_EMBEDDINGS) > 10:
        print(f"Preserving existing embeddings file at: {OUTPUT_EMBEDDINGS}")
    else:
        with open(OUTPUT_EMBEDDINGS, "wb") as file:
            pickle.dump(student_embeddings, file)
else:
    with open(OUTPUT_EMBEDDINGS, "wb") as file:
        pickle.dump(student_embeddings, file)
    print(f"Saved at: {OUTPUT_EMBEDDINGS}")

print("\nSFace embedding creation completed!")
print(f"Total students embedded: {len(student_embeddings)}")
print(f"Total images used: {total_images_used}")
print(f"Total failed images: {total_failed}")