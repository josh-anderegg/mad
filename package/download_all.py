#!/usr/bin/env python3
from pathlib import Path
import ee
import pandas as pd
import requests
import rasterio
import geopandas as gpd
import uuid
import os
import numpy as np
import json
import argparse
from shapely.geometry import box
from rasterio.features import rasterize
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('grid_path', help='Path to the grid to be downloaded.')
args = parser.parse_args()
GRID_PATH = args.grid_path
BASE_DIR = Path(__file__).resolve().parent.parent
ee.Authenticate()
ee.Initialize(project='siam-josh')  

boxes = pd.read_csv(GRID_PATH)

CHANNELS = ["B4", "B3", "B2", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "AOT"]

WORLD_COVER_MAP = {
    10: 'Tree cover',
    20: 'Shrubland',
    30: 'Grassland',
    40: 'Cropland',
    50: 'Built-up',
    60: 'Bare / sparse vegetation',
    70: 'Snow and ice',
    80: 'Permanent water bodies',
    90: 'Herbaceous wetland',
    95: 'Mangroves',
    100: 'Moss and lichen'
}

MAX_RETRIES = 1000

maus = gpd.read_file(BASE_DIR / 'data/maus/global_mining_polygons_v2.gpkg').to_crs(epsg=4326)
regions = gpd.read_file(BASE_DIR / "data/Ecoregions2017/Ecoregions2017.shp").to_crs(crs=4326)

def download_to(url, path):
    tries = 0
    response = None
    while tries < MAX_RETRIES:
        try:
            response = requests.get(url)
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
        except:
            tries += 1
    return False
        
def get_biome(box):
    intersecting = regions[regions.geometry.intersects(box)]
    if intersecting.empty:
        return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"
    
    return intersecting.iloc[0]['BIOME_NAME'], intersecting.iloc[0]['ECO_NAME'], intersecting.iloc[0]['BIOME_NUM'], intersecting.iloc[0]['OBJECTID']
    # TODO: Take the largest intersecting biome instead
    # intersecting = intersecting.copy()
    # intersecting["overlap_area"] = intersecting.geometry.intersection(box).area

    # best_match = intersecting.loc[intersecting["overlap_area"].idxmax()]

    # return best_match['BIOME_NAME'], best_match['ECO_NAME'], best_match['BIOME_NUM'], best_match['OBJECTID']

def process_tile(tile):
    gee_box = ee.geometry.Geometry.BBox(tile['min_lon'], tile['min_lat'], tile['max_lon'], tile['max_lat'])
    mid_lon = tile['max_lon'] + tile['min_lon'] / 2 
    mid_lat = tile['max_lat'] + tile['min_lat'] / 2
    img_string = BASE_DIR / f'data/images/SENTINEL2_{mid_lon:.6f}_{mid_lat:.6f}.tif'
    id_string = uuid.uuid4().hex
    temp_cov = BASE_DIR / f'data/temp/coverage_{id_string}.tif'
    temp_sat = BASE_DIR / f'data/temp/satellite_{id_string}.tif'

    image = ee.imagecollection.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")\
        .filterDate('2019-01-01', '2020-01-01') \
        .filterBounds(gee_box) \
        .filter(ee.filter.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))\
        .select(CHANNELS)\
        .median()\
    
    coverage_image = ee.imagecollection.ImageCollection("ESA/WorldCover/v100")\
        .filterBounds(gee_box)\
        .first()

    params = {
        'scale': 10,
        'region': gee_box,
        'format': 'GeoTIFF'
    }

    url = image.getDownloadURL(params)
    success_sat = download_to(url, temp_sat)
    
    esa_url = coverage_image.getDownloadURL(params)
    success_cov = download_to(esa_url, temp_cov)
    
    if not success_sat and success_cov:
        raise LookupError
    
    with rasterio.open(temp_cov) as esa_src:
        esa_data = esa_src.read(1).astype('uint8')
        # unique_values, counts = np.unique(esa_data, return_counts=True)
        world_cover_histogram = {}

        for code, label in WORLD_COVER_MAP.items():
            count = int(np.sum(esa_data == code))
            world_cover_histogram[label] = count
            
    with rasterio.open(temp_sat) as src:
        meta = src.meta.copy()
        transform = src.transform
        width, height = src.width, src.height
        crs = src.crs
        bounds = src.bounds
        bands_data = src.read() 
        
    bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bounds)], crs=crs)

    biome, ecoregion, biome_num, ecoregion_num = get_biome(box(*bounds))
    gdf_in_tile = gpd.overlay(maus.to_crs(crs), bbox_gdf, how='intersection')

    shapes = ((geom, 1) for geom in gdf_in_tile.geometry if geom.is_valid and not geom.is_empty)

    mine_mask = rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype='uint8'
    )

    meta.update({
        'count': bands_data.shape[0] + 1,
        'dtype': 'uint16' 
    })

    with rasterio.open(img_string, 'w', **meta) as dst:
        for i in range(bands_data.shape[0]):
            dst.write(bands_data[i], i + 1)

        dst.write(mine_mask, bands_data.shape[0] + 1)
        dst.set_band_description(1, 'B4: (Red)')
        dst.set_band_description(2, 'B3: (Green)')
        dst.set_band_description(3, 'B2: (Blue)')
        dst.set_band_description(4, 'B5: (Red Edge 1)')
        dst.set_band_description(5, 'B6: (Red Edge 2)')
        dst.set_band_description(6, 'B7: (Red Edge 3)')
        dst.set_band_description(7, 'B8: (Near Infrared)')
        dst.set_band_description(8, 'B8A: (Narrow Near Infrared)')
        dst.set_band_description(9, 'B9: (Water vapor)')
        dst.set_band_description(10, 'B11: (SWIR 1)')
        dst.set_band_description(11, 'B12: (SWIR 2)')
        dst.set_band_description(12, 'AOT: (Aerorosol Optical Thickness)')
        dst.set_band_description(13, 'Mine: (MAUS mining asset)')
        dst.update_tags(WORLD_COVER = json.dumps(world_cover_histogram))
        dst.update_tags(BIOME = biome)
        dst.update_tags(ECOREGION = ecoregion)
        dst.update_tags(BIOME_NUM = biome_num)
        dst.update_tags(ECOREGION_NUM = ecoregion_num)

    os.remove(temp_sat)
    os.remove(temp_cov)

tiles = [tile for _, tile in boxes.iterrows()]

results = []
with ProcessPoolExecutor(max_workers=8) as executor:
    for result in tqdm(executor.map(process_tile, tiles), total=len(tiles)):
        results.append(result)

