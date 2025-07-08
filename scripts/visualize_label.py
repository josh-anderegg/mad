#!python
import cv2
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('image_path', help='Path to the image to visualize.')
args = parser.parse_args()
PATH = args.image_path
txt_path = PATH.replace('.jpg', '.txt')
# Load image
image = cv2.imread(PATH)
height, width, _ = image.shape

# Read YOLO label
with open(txt_path, 'r') as f:
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

