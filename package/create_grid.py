import string
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import random
from package import BASE_DIR


MIN_OVERLAP_RATIO = None
NEGATIVE_INCLUSION_PROBABILITY = None
GRID_SIZE = None
SEED = None


def process_cell(coord, maus_path, regions_path, NEGATIVE_INCLUSION_PROBABILITY):
    global GRID_SIZE
    maus_gdf = gpd.read_file(maus_path).to_crs(
        epsg=3857
    )
    regions_gdf = gpd.read_file(regions_path).to_crs(
        epsg=3857
    )
    sindex = maus_gdf.sindex
    cell_area = GRID_SIZE * GRID_SIZE
    x, y = coord
    cell = box(x, y, x + GRID_SIZE, y + GRID_SIZE)

    # Local import of data for multiprocessing (GeoDataFrames are not picklable)
    local_gdf = maus_gdf
    local_sindex = sindex

    idxs = list(local_sindex.intersection(cell.bounds))
    # Insertion of negatives
    if not idxs:
        overlap = regions_gdf[regions_gdf.geometry.intersects(cell)]
        if not overlap.empty and random.random() < NEGATIVE_INCLUSION_PROBABILITY:  # Must not be ocean and pass a random check
            return cell
        return None

    candidates = local_gdf.geometry.iloc[idxs]  # type: ignore
    intersections = candidates.intersection(cell)
    overlap_area = sum(geom.area for geom in intersections if not geom.is_empty)

    if overlap_area / cell_area > MIN_OVERLAP_RATIO:
        return cell
    return None


def parse_args(args):
    global MIN_OVERLAP_RATIO, GRID_SIZE, SEED, NEGATIVE_INCLUSION_PROBABILITY
    RANDOM_SYMBOLS = string.ascii_letters + string.digits
    if args.random_seed is None:
        SEED = "".join(random.choices(RANDOM_SYMBOLS, k=32))
    else:
        SEED = args.random_seed

    random.seed(SEED)
    MIN_OVERLAP_RATIO = args.overlap_size
    GRID_SIZE = args.grid_size
    NEGATIVE_INCLUSION_PROBABILITY = args.negative_probability
    print(f"used seed: {SEED}")


def full_grid():
    global GRID_SIZE
    # Use the default borders for EPSG: 3857 https://epsg.io/3857
    minx, miny = -20037508.34, -20048966.1
    maxx, maxy = 20037508.34, 20048966.1

    x_coords = np.arange(minx, maxx, GRID_SIZE)
    y_coords = np.arange(miny, maxy, GRID_SIZE)
    return [(x, y) for x in x_coords for y in y_coords]


def filter_grid(grid):
    from itertools import repeat
    global NEGATIVE_INCLUSION_PROBABILITY
    maus_path = BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg"
    regions_path = BASE_DIR / "data/Ecoregions2017/Ecoregions2017.shp"
    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        for result in tqdm(executor.map(process_cell, grid, repeat(maus_path), repeat(regions_path), repeat(NEGATIVE_INCLUSION_PROBABILITY), chunksize=100000), total=len(grid)):
            if result is not None:
                results.append(result)
    return results


def output_grid(grid):
    global GRID_SIZE
    grid_gdf = gpd.GeoDataFrame({"geometry": grid}, crs="EPSG:3857").to_crs(
        "EPSG:4326"
    )
    # .gpkg ouput for visualization purposes
    grid_gdf.to_file(
        BASE_DIR / f"data/grids/grid_{SEED}_{GRID_SIZE}_epsg3857.gpkg",
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


def run(args):
    parse_args(args)
    global MIN_OVERLAP_RATIO, GRID_SIZE, SEED
    grid = full_grid()
    grid = filter_grid(grid)
    output_grid(grid)
