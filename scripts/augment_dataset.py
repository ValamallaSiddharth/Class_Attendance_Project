"""
Dataset augmentation utility for facial recognition datasets.
Applies transformations such as horizontal flips and brightness adjustments
to expand training face samples.
"""
import os
import cv2

DATASET_DIR = "dataset"


def augment_image(image):
    augmented = []
    # Horizontal flip
    augmented.append(cv2.flip(image, 1))

    # Brightness variations
    bright = cv2.convertScaleAbs(image, alpha=1.1, beta=10)
    dark = cv2.convertScaleAbs(image, alpha=0.9, beta=-10)
    augmented.extend([bright, dark])

    return augmented


def augment_dataset(input_dir=DATASET_DIR):
    if not os.path.exists(input_dir):
        print(f"Dataset directory '{input_dir}' not found.")
        return

    students = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    if not students:
        print(f"No student subdirectories found in '{input_dir}'.")
        return

    total_augmented = 0
    for student in students:
        student_dir = os.path.join(input_dir, student)
        images = [f for f in os.listdir(student_dir) if f.lower().endswith((".jpg", ".jpeg", ".png")) and not f.startswith("aug_")]
        for img_name in images:
            img_path = os.path.join(student_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue

            aug_imgs = augment_image(img)
            base_name, ext = os.path.splitext(img_name)
            for idx, aug_img in enumerate(aug_imgs):
                out_name = f"aug_{base_name}_{idx}{ext}"
                cv2.imwrite(os.path.join(student_dir, out_name), aug_img)
                total_augmented += 1

    print(f"Augmentation complete. Generated {total_augmented} augmented images.")


if __name__ == "__main__":
    augment_dataset()
