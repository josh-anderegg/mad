#!/usr/bin/env python3
import geopandas as gpd
# import matplotlib.pyplot as plt
from shapely.geometry import box
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm 
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--grid-size", type=int, default=5500, help="Define the size of the grid in m (default: 5500)")
parser.add_argument("-o", "--overlap-size", type=float, default=0.00001, help="Define mininmal overlap in point percentage (default: 0.00001 = 0.1%)")

args = parser.parse_args()

MIN_OVERLAP_RATIO = args.overlap_size
GRID_SIZE = args.grid_size  # (m) 10 km in meters

# Project it to a even metric representation
gdf = gpd.read_file('data/maus/global_mining_polygons_v2.gpkg').to_crs(epsg=3857)
sindex = gdf.sindex
biomes = gpd.read_file('data/Ecoregions2017/Ecoregions2017.shp').to_crs(epsg=3857)
# Use the default borders for EPSG: 3857 https://epsg.io/3857
minx, miny = -20037508.34, -20048966.1
maxx, maxy =  20037508.34,  20048966.1
 
cell_area = GRID_SIZE * GRID_SIZE


def process_cell(coord):
    x, y = coord
    cell = box(x, y, x + GRID_SIZE, y + GRID_SIZE)

    # Local import of data for multiprocessing (GeoDataFrames are not picklable)
    local_sindex = sindex

    idxs = list(local_sindex.intersection(cell.bounds))
    if len(idxs) > 0:
        return None

    overlap = biomes[biomes.geometry.intersects(cell)]

    if overlap.empty:
        return None

    if len(overlap) == 1:
        return {"biome": overlap['BIOME_NAME'], "geometry": cell}
    
    overlap = overlap.copy()
    overlap["overlap_area"] = overlap.geometry.intersection(cell).area

    best_match = overlap.loc[overlap["overlap_area"].idxmax()]
    return {"biome": best_match['BIOME_NAME'], "geometry": cell}

x_coords = np.arange(minx, maxx, GRID_SIZE)
y_coords = np.arange(miny, maxy, GRID_SIZE)
all_coords = [(x, y) for x in x_coords for y in y_coords]

results = []
with ProcessPoolExecutor() as executor:
    for result in tqdm(executor.map(process_cell, all_coords, chunksize=100000), total=len(all_coords)):
        results.append(result)

grid_cells = [cell for cell in results if cell is not None]

grid_gdf = gpd.GeoDataFrame(grid_cells, crs='EPSG:3857').to_crs('EPSG:4326')
grid_gdf.to_file(f"data/grids/grid_{GRID_SIZE}_epsg3857.gpkg", layer='squares_layer', driver="GPKG")
grid_gdf['min_lon'] = grid_gdf.bounds.minx
grid_gdf['max_lon'] = grid_gdf.bounds.maxx
grid_gdf['min_lat'] = grid_gdf.bounds.miny
grid_gdf['max_lat'] = grid_gdf.bounds.maxy

grid_gdf[['min_lon', 'min_lat', 'max_lon', 'max_lat', 'biome']].to_csv(f'data/grids/grid_neg_{GRID_SIZE}_epsg3857.csv')