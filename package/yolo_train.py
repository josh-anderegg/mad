from package import BASE_DIR
from pathlib import Path
from ultralytics import YOLO
import os

DATASET_PATH = None
OUTPUT_PATH = None
REMAINING_ARGUMENTS = None


def parse_args(args):
    global DATASET_PATH, OUTPUT_PATH, REMAINING_ARGUMENTS
    DATASET_PATH = args.dataset
    OUTPUT_PATH = args.output
    if OUTPUT_PATH is None:
        path = Path(DATASET_PATH)
        OUTPUT_PATH = BASE_DIR / f"outputs/{path.name}"
        os.mkdir(OUTPUT_PATH)
    REMAINING_ARGUMENTS = args.arguments


def run(args):
    parse_args(args)
    model = YOLO("yolo11n.pt")

    model.train(
        data=f"{DATASET_PATH}/.dataset.yaml", imgsz=620, batch=64, project=OUTPUT_PATH
    )
