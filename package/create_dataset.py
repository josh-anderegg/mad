from osgeo import gdal
from shapely.validation import make_valid
import os
import random
import string
import rasterio
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import geopandas as gpd
import numpy as np
from shapely.geometry import box
from tqdm import tqdm
from itertools import repeat
from rasterio.windows import Window
import warnings
warnings.filterwarnings(
    "ignore",
    message="invalid value encountered in make_valid",
    category=RuntimeWarning
)
gdal.UseExceptions()
RANDOM_SYMBOLS = string.ascii_letters + string.digits
MAUS_PATH = None
OUTPUT_PATH = None
DATABASE_PATH = None
SEED = None
FILTERS = None
EXPANSIONS = None
BLAME_BOARD = None


def label(src, win, lbl_path, maus_df):
    results = []
    raster_bounds = box(*rasterio.windows.bounds(win, src.transform))

    image_minx, image_miny, image_maxx, image_maxy = raster_bounds.bounds
    image_width = image_maxx - image_minx
    image_height = image_maxy - image_miny

    sindex = maus_df.sindex
    candidate_idx = list(sindex.intersection(raster_bounds.bounds))
    candidates = maus_df.iloc[candidate_idx]

    for geom in candidates.geometry:
        try:
            if not geom.is_valid:
                geom = make_valid(geom)
            if geom.is_empty:
                continue
            if not np.isnan(geom.bounds).any() and geom.intersects(raster_bounds):
                intersection = geom.intersection(raster_bounds)
                if intersection.is_empty:
                    continue

                minx, miny, maxx, maxy = intersection.bounds
                center_x = (minx + maxx) / 2
                center_y = (miny + maxy) / 2
                rel_center_x = (center_x - image_minx) / image_width
                rel_center_y = 1 - (center_y - image_miny) / image_height
                rel_width = (maxx - minx) / image_width
                rel_height = (maxy - miny) / image_height

                results.append((rel_center_x, rel_center_y, rel_width, rel_height))
        except Exception:
            continue

    with open(lbl_path, 'w') as dst:
        for cx, cy, lx, ly in results:
            dst.write(f'0 {cx} {cy} {lx} {ly}\n')


def extract(src, win, img_path):
    minx, miny, maxx, maxy = rasterio.windows.bounds(win, src.transform)
    projWin = [minx, maxy, maxx, miny]
    translate_options = gdal.TranslateOptions(
        format='JPEG',
        bandList=[1, 2, 3],
        outputType=gdal.GDT_Byte,
        scaleParams=[[0, 255]],
        width=620,
        height=620,
        projWin=projWin,
        creationOptions=['QUALITY=98']
    )
    gdal.Translate(destName=img_path, srcDS=src.name, options=translate_options)


def contains_nodata(src, win) -> bool:
    data = src.read(window=win)

    nodata = src.nodata

    if nodata is not None:
        mask = np.any(data == nodata, axis=0)
    else:
        mask = np.all(data == 0, axis=0)

    if np.any(mask):
        return True

    return False


def contains_polygons(src, win, maus_df) -> bool:
    raster_bounds = box(*rasterio.windows.bounds(win, src.transform))

    sindex = maus_df.sindex
    if sindex is None:
        return False

    candidate_idx = list(sindex.intersection(raster_bounds.bounds))
    if not candidate_idx:
        return False

    candidates = maus_df.iloc[candidate_idx]
    for geom in candidates.geometry:
        try:
            if not geom.is_valid:
                geom = make_valid(geom)
            if geom.is_empty:
                continue
            if not np.isnan(geom.bounds).any() and geom.intersects(raster_bounds):
                intersection = geom.intersection(raster_bounds)
                if not intersection.is_empty:
                    return True
        except Exception:
            continue
    return False


def process_window(src, win, name, sub, maus_df):
    global OUTPUT_PATH

    lbl_path = f"{OUTPUT_PATH}/labels/{sub}/{name}.txt"
    img_path = f"{OUTPUT_PATH}/images/{sub}/{name}.jpg"
    extract(src, win, img_path)
    label(src, win, lbl_path, maus_df)


INCLUSION_PROBABILITY = 0.005


def filter_map(src, windows, filter_func, maus_df):
    quality_failures = set()
    ret_windows = []
    for name, window in windows:
        if contains_nodata(src, window):
            quality_failures.add("MISSING_DATA")
            continue
        if not contains_polygons(src, window, maus_df):
            if random.random() < INCLUSION_PROBABILITY:
                ret_windows.append((name, window))
            continue
        else:
            ret_windows.append((name, window))
    return (quality_failures, ret_windows)


def simple_grid(image_path, tile_size=1000):
    with rasterio.open(image_path) as src:
        width = src.width
        height = src.height
    name = image_path.split('/')[-1].replace('.jp2', '')
    count = 0
    windows = []
    for top in range(0, height, tile_size):
        for left in range(0, width, tile_size):
            window = Window(left, top, tile_size, tile_size)
            windows.append((f"{name}_{count}", window))
            count += 1
    return windows


def process_image(image_path, sub):
    global OUTPUT_PATH, MAUS_PATH, FILTERS, EXPANSIONS

    with rasterio.open(image_path) as src:
        # Create the overall grid of windows
        windows = simple_grid(image_path)

        maus_df = gpd.read_file(MAUS_PATH).to_crs(src.crs)

        # Filter and collec the malfunctions for the blame
        quality_failures, windows = filter_map(src, windows, None, maus_df)

        for tile_name, window in windows:
            process_window(src, window, tile_name, sub, maus_df)

        return quality_failures


def process_images(sub, images):
    global DATABASE_PATH, BLAME_BOARD
    quality_failures = []

    print(f"Processing {sub} images")
    with ProcessPoolExecutor(max_workers=3) as executor:
        results = executor.map(process_image, [f"{DATABASE_PATH}/{image}" for image in images], repeat(sub))
        for image, quality_failure in tqdm(zip(images, results), total=len(images)):
            quality_failures.append((image, quality_failure))

    with open(BLAME_BOARD, "a") as blame_file:
        for (file, failures) in quality_failures:
            if len(failures) < 1:
                continue
            blame_file.write(f"{file} {' '.join(failures)}\n")


def init_directory():
    global OUTPUT_PATH
    try:
        os.makedirs(OUTPUT_PATH, exist_ok=False)
    except Exception:
        raise FileExistsError(f"Directory {OUTPUT_PATH} already exists.")
    with open(f"{OUTPUT_PATH}/dataset.yaml", "w") as f:
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
            os.makedirs(f"{OUTPUT_PATH}/{sup}/{sub}")


def get_split():
    with open(f"{DATABASE_PATH}/train.txt", "r") as file:
        train_images = [line.strip() for line in file]

    with open(f"{DATABASE_PATH}/val.txt", "r") as file:
        val_images = [line.strip() for line in file]

    with open(f"{DATABASE_PATH}/test.txt", "r") as file:
        test_images = [line.strip() for line in file]

    return train_images, val_images, test_images


def parse_args(args):
    global MAUS_PATH, OUTPUT_PATH, DATABASE_PATH, SEED, FILTERS, EXPANSIONS, BLAME_BOARD

    if args.random_seed is None:
        SEED = "".join(random.choices(RANDOM_SYMBOLS, k=32))
    else:
        SEED = args.seed

    now = datetime.now()
    print(f"Using seed: {SEED}")
    OUTPUT_PATH = args.path
    DATABASE_PATH = args.database
    MAUS_PATH = args.maus
    FILTERS = args.filters
    EXPANSIONS = args.expansions
    BLAME_BOARD = f"{DATABASE_PATH}/blame_{now.strftime("%Y_%m_%d_%H_%M")}.txt"


def run(args):
    parse_args(args)
    global SEED, OUTPUT_PATH
    random.seed(SEED)

    init_directory()
    train_images, val_images, test_images = get_split()
    print("Processing training images")
    process_images("train", train_images)
    print("Processing validation images")
    process_images("val", val_images)
    print("Processing test images")
    process_images("test", test_images)
