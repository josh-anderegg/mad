#!/bin/python3
import argparse
import os
import random
import string
from label_images import label_all

RANDOM_SYMBOLS = string.ascii_letters + string.digits

def init_directory(dataset_path):
    try:
        os.makedirs(dataset_path, exist_ok=False)
    except Exception:
        raise FileExistsError(f"Directory {dataset_path} already exists.")
    with open(f"{dataset_path}/dataset.yaml", "w") as f:
        f.write(
            """
train: ./images/train
val: ./images/val
test: ./images/test

nc: 1
names:
  0: mine
        """
        )
    for sup in ["images", "labels"]:
        for sub in ["train", "val", "test"]:
            os.makedirs(f"{dataset_path}/{sup}/{sub}")


def create_split(images_path, seed):
    images = os.listdir(images_path)
    train_percentage, val_percentage, test_percentage = 0.7, 0.2, 0.1
    train_count, val_count, test_count = 0.7, 0.2, 0.1

    random.shuffle(images)
    train_images = images[:]
     

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Output path to the final dataset")
    parser.add_argument("images", help="Path to the .tif images to be labeled")
    parser.add_argument("--maus", "-m", help="Path to the maus .gpkg set")
    parser.add_argument("--seed", "-s", help="Random seed for the split")
    args = parser.parse_args()
    if args.random_seed is None:
        SEED = ''.join(random.choices(RANDOM_SYMBOLS, k=32))
    else:
        SEED = args.seed
    random.seed(SEED)

    DATASET_PATH = args.path
    init_directory(DATASET_PATH)
