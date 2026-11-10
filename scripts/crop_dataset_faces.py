import cv2
import os

# ============================================================
# PATHS
# ============================================================

INPUT_DATASET = "dataset"
OUTPUT_DATASET = "cropped_dataset"

# ============================================================
# SETTINGS
# ============================================================

FACE_SIZE = 200
PADDING = 25

os.makedirs(OUTPUT_DATASET, exist_ok=True)

# ============================================================
# FACE DETECTOR
# ============================================================

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if face_detector.empty():
    print("Error: Haar cascade not loaded.")
    exit()


def detect_largest_face(img):
    """
    Detects largest face from original image.
    Uses grayscale only for detection, but returns color crop.
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.equalizeHist(gray)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    if len(faces) == 0:
        return None

    largest_face = max(
        faces,
        key=lambda face: face[2] * face[3]
    )

    return largest_face


def crop_color_face(img, face_box):
    """
    Crops face from color image and saves it in color.
    """

    x, y, w, h = face_box

    img_h, img_w = img.shape[:2]

    x1 = max(0, x - PADDING)
    y1 = max(0, y - PADDING)
    x2 = min(img_w, x + w + PADDING)
    y2 = min(img_h, y + h + PADDING)

    face_crop = img[y1:y2, x1:x2]

    face_crop = cv2.resize(
        face_crop,
        (FACE_SIZE, FACE_SIZE)
    )

    return face_crop


# ============================================================
# PROCESS DATASET
# ============================================================

total_saved = 0
total_failed = 0

for roll_no in sorted(os.listdir(INPUT_DATASET)):

    student_input_path = os.path.join(INPUT_DATASET, roll_no)

    if not os.path.isdir(student_input_path):
        continue

    student_output_path = os.path.join(OUTPUT_DATASET, roll_no)
    os.makedirs(student_output_path, exist_ok=True)

    print(f"\nProcessing: {roll_no}")

    saved_count = 0
    failed_count = 0

    for image_name in os.listdir(student_input_path):

        if not image_name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(student_input_path, image_name)

        img = cv2.imread(image_path)

        if img is None:
            print(f"Could not read: {image_path}")
            failed_count += 1
            continue

        face_box = detect_largest_face(img)

        if face_box is None:
            print(f"No face found: {image_path}")
            failed_count += 1
            continue

        face_crop = crop_color_face(img, face_box)

        base_name = os.path.splitext(image_name)[0]

        output_path = os.path.join(
            student_output_path,
            f"{base_name}_face.jpg"
        )

        cv2.imwrite(output_path, face_crop)

        saved_count += 1

    print(f"Color faces cropped for {roll_no}: {saved_count}")
    print(f"Failed images for {roll_no}: {failed_count}")

    total_saved += saved_count
    total_failed += failed_count

print("\nColor face cropping completed!")
print(f"Total color cropped faces saved: {total_saved}")
print(f"Total failed images: {total_failed}")
print(f"Color cropped dataset saved in: {OUTPUT_DATASET}")
