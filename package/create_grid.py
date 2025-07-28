import string
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import random
from package import BASE_DIR


MIN_OVERLAP_RATIO = None
NEGATIVE_INCLUSION_PROBABILITY = None
GRID_SIZE = None
SEED = None


def process_cell(coord, NEGATIVE_INCLUSION_PROBABILITY):
    global GRID_SIZE, maus_gdf, regions_gdf

    cell_area = GRID_SIZE * GRID_SIZE
    x, y = coord
    cell = box(x, y, x + GRID_SIZE, y + GRID_SIZE)

    # Local import of data for multiprocessing (GeoDataFrames are not picklable)
    # local_gdf = maus_gdf
    # local_sindex = sindex

    idxs = list(maus_gdf.sindex.intersection(cell.bounds))
    # Insertion of negatives
    if not idxs:
        overlap = regions_gdf[regions_gdf.geometry.intersects(cell)]
        if not overlap.empty and random.random() < NEGATIVE_INCLUSION_PROBABILITY:  # Must not be ocean and pass a random check
            return cell
        return None

    if MIN_OVERLAP_RATIO == 0:
        return cell
    candidates = maus_gdf.geometry.iloc[idxs]  # type: ignore
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


def init_worker(maus_path, regions_path):
    global maus_gdf, regions_gdf
    maus_gdf = gpd.read_file(maus_path).to_crs(
        epsg=3857
    )
    regions_gdf = gpd.read_file(regions_path).to_crs(
        epsg=3857
    )


def chunked_iterable(iterable, chunk_size):
    """Yield successive chunk_size-sized lists from iterable."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def generate_grid():
    global NEGATIVE_INCLUSION_PROBABILITY, GRID_SIZE
    maus_path = BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg"
    regions_path = BASE_DIR / "data/Ecoregions2017/Ecoregions2017.shp"

    minx, miny = -20037508.34, -20048966.1
    maxx, maxy = 20037508.34, 20048966.1

    x_coords = np.arange(minx, maxx, GRID_SIZE)
    y_coords = np.arange(miny, maxy, GRID_SIZE)
    grid = ((x, y) for x in x_coords for y in y_coords)

    results = []
    chunk_size = 1000
    total_cells = len(x_coords) * len(y_coords)
    total_chunks = (total_cells + chunk_size - 1) // chunk_size
    with ProcessPoolExecutor(max_workers=14, initializer=init_worker, initargs=(maus_path, regions_path)) as executor:
        for chunk in tqdm(chunked_iterable(grid, chunk_size), total=total_chunks, desc="Chunks processed"):
            futures = [executor.submit(process_cell, cell, NEGATIVE_INCLUSION_PROBABILITY) for cell in chunk]
            for f in as_completed(futures):
                result = f.result()
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
    grid = generate_grid()
    output_grid(grid)
