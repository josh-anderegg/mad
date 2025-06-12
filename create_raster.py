import geopandas as gpd
# import matplotlib.pyplot as plt
from shapely.geometry import box
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm 
MIN_OVERLAP_RATIO = 0.00001
GRID_SIZE = 10_000  # (m) 10 km in meters

# Project it to a even metric representation
gdf = gpd.read_file('input/maus/global_mining_polygons_v2.gpkg').to_crs(epsg=6933)
sindex = gdf.sindex

# Use the default borders for EPSG: 6933
minx, miny, maxx, maxy = -17367530, -7314540, 17367530, 7314540
cell_area = GRID_SIZE * GRID_SIZE


def process_cell(coord):
    x, y = coord
    cell = box(x, y, x + GRID_SIZE, y + GRID_SIZE)

    # Local import of data for multiprocessing (GeoDataFrames are not picklable)
    local_gdf = gdf
    local_sindex = sindex

    idxs = list(local_sindex.intersection(cell.bounds))
    if not idxs:
        return None

    candidates = local_gdf.geometry.iloc[idxs] # type: ignore
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
    for result in tqdm(executor.map(process_cell, all_coords, chunksize=1000), total=len(all_coords)):
        results.append(result)

grid_cells = [cell for cell in results if cell is not None]

grid_gdf = gpd.GeoDataFrame({'geometry': grid_cells}, crs='EPSG:6933').to_crs('EPSG:4326')
grid_gdf.to_file("squares.gpkg", layer='squares_layer', driver="GPKG")
grid_gdf['min_lon'] = grid_gdf.bounds.minx
grid_gdf['max_lon'] = grid_gdf.bounds.maxx
grid_gdf['min_lat'] = grid_gdf.bounds.miny
grid_gdf['max_lat'] = grid_gdf.bounds.maxy

grid_gdf[['min_lon', 'min_lat', 'max_lon', 'max_lat']].to_csv('grid_boxes.csv')