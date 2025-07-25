from osgeo import gdal
import os
import random
import string
import rasterio
from concurrent.futures import ProcessPoolExecutor
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm
from itertools import repeat
gdal.UseExceptions()
RANDOM_SYMBOLS = string.ascii_letters + string.digits
MAUS_PATH = None
OUTPUT_PATH = None
IMAGES_PATH = None
SEED = None


def label(file_path, output_path, maus_df):
    name = file_path.split('/')[-1].replace('.tif', '')

    lbl_file = f'{output_path}/{name}.txt'

    results = []
    with rasterio.open(file_path) as src:
        raster_bounds = box(*src.bounds)
        raster_crs = src.crs

        image_minx, image_miny, image_maxx, image_maxy = src.bounds
        image_width = image_maxx - image_minx
        image_height = image_maxy - image_miny

        # Reproject only once
        gdf_proj = maus_df.to_crs(raster_crs)

        # Build spatial index once
        sindex = gdf_proj.sindex

        # Use sindex to get relevant geometries
        possible_matches_index = list(sindex.intersection(raster_bounds.bounds))
        possible_matches = gdf_proj.iloc[possible_matches_index]  # type: ignore

        for _, row in possible_matches.iterrows():
            poly = row.geometry
            if poly.intersects(raster_bounds):
                intersection = poly.intersection(raster_bounds)
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

    with open(lbl_file, 'w') as dst:
        for cx, cy, lx, ly in results:
            dst.write(f'0 {cx} {cy} {lx} {ly}\n')


def label_images(label_path, images):
    global MAUS_PATH

    maus_df = gpd.read_file(MAUS_PATH)
    with ProcessPoolExecutor(max_workers=16) as executor:
        for result in tqdm(executor.map(label, [f"{IMAGES_PATH}/{image}" for image in images], repeat(label_path), repeat(maus_df)), total=len(images)):
            pass


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


def extract(image, output, bands=[]):
    base = image.split('/')[-1].replace('.tif', '')
    jpg_path = f"{output}/{base}.jpg"
    translate_options = gdal.TranslateOptions(
        format='JPEG',
        bandList=[1, 2, 3],
        outputType=gdal.GDT_Byte,
        scaleParams=[[0, 255]],  # Auto scale full range
        width=512,
        height=512
    )
    gdal.Translate(destName=str(jpg_path), srcDS=str(image), options=translate_options)


def extract_images(images, output, bands=[]):
    with ProcessPoolExecutor(max_workers=16) as executor:
        for result in tqdm(executor.map(extract, [f"{IMAGES_PATH}/{image}" for image in images], repeat(output), repeat(bands)), total=len(images)):
            pass


def create_split():
    images = os.listdir(IMAGES_PATH)
    image_count = len(images)
    train_percentage, val_percentage, test_percentage = 0.7, 0.2, 0.1
    train_count, val_count, test_count = int(train_percentage * image_count), int(val_percentage * image_count), int(test_percentage * image_count)

    random.shuffle(images)
    train_images = images[:train_count]
    val_images = images[train_count:train_count + val_count]
    test_images = images[train_count + val_count:]

    return train_images, val_images, test_images


def parse_args(args):
    global MAUS_PATH, OUTPUT_PATH, IMAGES_PATH, SEED

    if args.random_seed is None:
        SEED = "".join(random.choices(RANDOM_SYMBOLS, k=32))
    else:
        SEED = args.seed

    print(f"Using seed: {SEED}")
    OUTPUT_PATH = args.path
    IMAGES_PATH = args.images
    MAUS_PATH = args.maus


def run(args):
    parse_args(args)
    global SEED, OUTPUT_PATH
    random.seed(SEED)

    init_directory()
    train_images, val_images, test_images = create_split()
    print("Creating train labels")
    label_images(f"{OUTPUT_PATH}/labels/train", train_images)
    print("Creating validation labels")
    label_images(f"{OUTPUT_PATH}/labels/val", val_images)
    print("Creating test labels")
    label_images(f"{OUTPUT_PATH}/labels/test", test_images)

    print("Transforming train images")
    extract_images(train_images, f"{OUTPUT_PATH}/images/train")
    print("Transforming validation images")
    extract_images(val_images, f"{OUTPUT_PATH}/images/val")
    print("Transforming test images")
    extract_images(test_images, f"{OUTPUT_PATH}/images/test")
