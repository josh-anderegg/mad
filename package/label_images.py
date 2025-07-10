from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box
import os

from tqdm import tqdm
BASE_DIR = Path(__file__).resolve().parent.parent
gdf = gpd.read_file(BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg")

# TODO Maybe put this as an argument?
DIR = BASE_DIR / 'data/images'
def label(name):
    name = name.replace('.tif', '')

    tif_file = f'{DIR}/{name}.tif'
    lbl_file = BASE_DIR / f'data/labels/{name}.txt'
    results = []

    with rasterio.open(tif_file) as src:
        raster_bounds = box(*src.bounds)
        raster_crs = src.crs

        image_minx, image_miny, image_maxx, image_maxy = src.bounds
        image_width = image_maxx - image_minx
        image_height = image_maxy - image_miny

        # Reproject only once
        gdf_proj = gdf.to_crs(raster_crs)

        # Build spatial index once
        sindex = gdf_proj.sindex

        # Use sindex to get relevant geometries
        possible_matches_index = list(sindex.intersection(raster_bounds.bounds))
        possible_matches = gdf_proj.iloc[possible_matches_index] # type: ignore

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

with ProcessPoolExecutor(max_workers=16) as executor:
    for result in tqdm(executor.map(label, os.listdir(DIR)), total=len(os.listdir(DIR))):
        pass
