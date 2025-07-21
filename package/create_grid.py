#!/usr/bin/env python3
from pathlib import Path
import string
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import argparse
import random

BASE_DIR = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser()
parser.add_argument(
    "-g",
    "--grid-size",
    type=int,
    default=5500,
    help="Define the size of the grid in m (default: 5500)",
)
parser.add_argument(
    "-o",
    "--overlap-size",
    type=float,
    default=0.00001,
    help="Define mininmal overlap in point percentage (default: 0.00001 = 0.1%)",
)
parser.add_argument(
    "-r",
    "--random-seed",
    type=str,
    default=None,
    help="Random string used for all the randomization done.",
)

args = parser.parse_args()

RANDOM_SYMBOLS = string.ascii_letters + string.digits
if args.random_seed is None:
    SEED = "".join(random.choices(RANDOM_SYMBOLS, k=32))
else:
    SEED = args.random_seed

MIN_OVERLAP_RATIO = args.overlap_size
GRID_SIZE = args.grid_size
print(f"used seed: {SEED}")

# Project it to an equidistant gridlike projection
gdf = gpd.read_file(BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg").to_crs(
    epsg=3857
)
biomes = gpd.read_file(BASE_DIR / "data/Ecoregions2017/Ecoregions2017.shp").to_crs(
    epsg=3857
)
sindex = gdf.sindex

# Use the default borders for EPSG: 3857 https://epsg.io/3857
minx, miny = -20037508.34, -20048966.1
maxx, maxy = 20037508.34, 20048966.1

cell_area = GRID_SIZE * GRID_SIZE


def process_cell(coord):
    x, y = coord
    cell = box(x, y, x + GRID_SIZE, y + GRID_SIZE)

    # Local import of data for multiprocessing (GeoDataFrames are not picklable)
    local_gdf = gdf
    local_sindex = sindex

    idxs = list(local_sindex.intersection(cell.bounds))
    # Insertion of negatives
    if not idxs:
        overlap = biomes[biomes.geometry.intersects(cell)]
        if (
            not overlap.empty and random.randrange(100) < 5
        ):  # Must not be ocean and pass 5% chance
            return cell
        return None

    candidates = local_gdf.geometry.iloc[idxs]  # type: ignore
    intersections = candidates.intersection(cell)
    overlap_area = sum(geom.area for geom in intersections if not geom.is_empty)

    if overlap_area / cell_area > MIN_OVERLAP_RATIO:
        return cell
    return None


x_coords = np.arange(minx, maxx, GRID_SIZE)
y_coords = np.arange(miny, maxy, GRID_SIZE)
all_coords = [(x, y) for x in x_coords for y in y_coords]

results = []
with ProcessPoolExecutor() as executor:
    for result in tqdm(
        executor.map(process_cell, all_coords, chunksize=100000), total=len(all_coords)
    ):
        results.append(result)

grid_cells = [cell for cell in results if cell is not None]

grid_gdf = gpd.GeoDataFrame({"geometry": grid_cells}, crs="EPSG:3857").to_crs(
    "EPSG:4326"
)
grid_gdf.to_file(
    BASE_DIR / f"data/grids/grid_{GRID_SIZE}_epsg3857.gpkg",
    layer="squares_layer",
    driver="GPKG",
)
grid_gdf["min_lon"] = grid_gdf.bounds.minx
grid_gdf["max_lon"] = grid_gdf.bounds.maxx
grid_gdf["min_lat"] = grid_gdf.bounds.miny
grid_gdf["max_lat"] = grid_gdf.bounds.maxy

grid_gdf[["min_lon", "min_lat", "max_lon", "max_lat"]].to_csv(
    BASE_DIR / f"data/grids/grid_{SEED}_{GRID_SIZE}_epsg3857.csv"
)
