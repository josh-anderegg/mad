#!python
import cv2
import argparse

# Given a
parser = argparse.ArgumentParser()
parser.add_argument('image_path', help='Path to the image to visualize.')
parser.add_argument('description_path', help='Path to the the class description.')
args = parser.parse_args()
IMG_PATH = args.image_path
TXT_PATH = args.image_path

# Load image
image = cv2.imread(IMG_PATH)
height, width, _ = image.shape

# Read YOLO label
with open(TXT_PATH, 'r') as f:
    lines = f.readlines()

for line in lines:
    class_id, x_center, y_center, w, h = map(float, line.split())
    
    # Convert to absolute coordinates
    x_center *= width
    y_center *= height
    w *= width
    h *= height
    
    x1 = int(x_center - w / 2)
    y1 = int(y_center - h / 2)
    x2 = int(x_center + w / 2)
    y2 = int(y_center + h / 2)
    
    # Draw rectangle
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, f'Class {int(class_id)}', (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cv2.imshow("Labeled Image", image); cv2.waitKey(0)

