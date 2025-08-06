import numpy as np
import cv2
import tifffile
import random

def random_crop_rotate_tif(image_path, output_size=256, max_trials=100):
    # Load the multi-channel TIF
    img = tifffile.imread(image_path)  # Shape: (H, W, 16)
    # if img.ndim != 3 or img.shape[2] != 16:
    #     raise ValueError("Expected a 16-channel TIF image.")

    h, w, c = img.shape
    # assert c == 16

    for _ in range(max_trials):
        # Random angle between 0-360 degrees
        angle = random.uniform(0, 360)
        # Random scale between 0.8x and 1.2x of output size
        size = int(output_size * random.uniform(0.8, 1.2))
        half_size = size // 2

        # Compute size of bounding box after rotation
        rot_rad = np.deg2rad(angle)
        cos = np.abs(np.cos(rot_rad))
        sin = np.abs(np.sin(rot_rad))
        bbox_w = int(size * cos + size * sin)
        bbox_h = int(size * sin + size * cos)

        # Choose center that keeps rotated crop inside bounds
        cx = random.randint(bbox_w//2, w - bbox_w//2)
        cy = random.randint(bbox_h//2, h - bbox_h//2)

        # Build affine transform
        rot_matrix = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)

        # Apply rotation to the full image (each channel separately)
        rotated = np.stack([
            cv2.warpAffine(img[..., i], rot_matrix, (w, h), flags=cv2.INTER_LINEAR)
            for i in range(c)
        ], axis=-1)

        # Crop from the rotated image
        x1, y1 = cx - half_size, cy - half_size
        x2, y2 = cx + half_size, cy + half_size

        if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
            continue  # Try again if out of bounds

        crop = rotated[y1:y2, x1:x2, :]

        if crop.shape[:2] == (size, size):
            return crop  # Return one valid crop

    raise RuntimeError("Failed to find a valid crop within max_trials")

# Example usage
# crop = random_crop_rotate_tif("your_image.tif", output_size=256)
# tifffile.imwrite("cropped_output.tif", crop)

crop = random_crop_rotate_tif('/run/media/cynik/Elements/s2-images/10SFK.tif', output_size=512)
tifffile.imwrite("cropped_output.tif", crop)
