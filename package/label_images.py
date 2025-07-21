#!/bin/python3
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import geopandas as gpd
import rasterio
from shapely.geometry import box
import os
from tqdm import tqdm
import argparse


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


def label_all(IMAGE_PATH, LABEL_PATH, MAUS_PATH):
    from itertools import repeat
    maus_df = gpd.read_file(MAUS_PATH)
    with ProcessPoolExecutor(max_workers=16) as executor:
        for result in tqdm(executor.map(label, [f"{IMAGE_PATH}/{image}" for image in os.listdir(IMAGE_PATH)], repeat(LABEL_PATH), repeat(maus_df)), total=len(os.listdir(IMAGE_PATH))):
            pass


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("images_path", help="Path to the .tif images")
    parser.add_argument("label_path", help="Path to the output directory")
    parser.add_argument("--maus", "-m", default=BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg", help="Path to the .tif images")
    args = parser.parse_args()
    IMAGE_PATH = args.images_path
    LABEL_PATH = args.label_path
    MAUS_PATH = args.maus
    os.makedirs(LABEL_PATH)
    label_all(IMAGE_PATH, LABEL_PATH, MAUS_PATH)
