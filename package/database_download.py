from package import BASE_DIR, random_seed
import glob
from datetime import datetime
from tqdm import tqdm
import os
import geopandas as gpd
import random
import subprocess

DATABASE_PATH = None
BANDS = None
IMAGECOUNT = None
COMPOSITION = None
BAND_TRANSLATION = {
    "TCI": "R10m/TCI.jp2",
    "B2": "R10m/B02.jp2",
    "B3": "R10m/B03.jp2",
    "B4": "R10m/B04.jp2",
    "B5": "R20m/B05.jp2",
    "B6": "R20m/B06.jp2",
    "B7": "R20m/B07.jp2",
    "B8": "R10m/B08.jp2",
    "B8A": "R20m/B8A.jp2",
    "B9": "R60m/B09.jp2",
    "B11": "R20m/B11.jp2",
    "B12": "R20m/B12.jp2",
    "AOT": "R10m/AOT.jp2",
}


def parse_args(args):
    global DATABASE_PATH, BANDS, IMAGECOUNT, COMPOSITION
    DATABASE_PATH = f"{args.datapath}"
    BANDS = list(map(lambda x: BAND_TRANSLATION[x], args.bands))
    IMAGECOUNT = args.image_count
    COMPOSITION = args.composition


def process_tile(name):
    global COMPOSITION, DATABASE_PATH

    match COMPOSITION:
        case "first":
            subprocess.run([BASE_DIR / "package/s3_image_download_first.sh", name, DATABASE_PATH, *BANDS,])
        case "layered":
            pass
        case "pixels":
            pass


def get_all_images():
    global DATABASE_PATH
    with open(f"{DATABASE_PATH}/tiles.txt") as f:
        all_tiles = f.read().splitlines()

    for tile in tqdm(all_tiles, desc="Downloading images"):
        process_tile(tile)


def collect_logs():
    global DATABASE_PATH

    now = datetime.now()
    timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")
    log_files = sorted(glob.glob(f"{DATABASE_PATH}/*_downloading.tlog"))
    with open(os.path.join(DATABASE_PATH, f"{timestamp}_downloading.log"), "w") as outfile:
        for fname in log_files:
            with open(fname) as infile:
                outfile.write(infile.read())

    for fname in log_files:
        os.remove(fname)


def run(args):
    parse_args(args)
    get_all_images()
    collect_logs()
