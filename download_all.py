#!/usr/bin/env python3
import ee
import pandas as pd
import requests
import rasterio
import geopandas as gpd
from shapely.geometry import box
from rasterio.features import rasterize
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

ee.Authenticate()
ee.Initialize(project='siam-josh')  

boxes = pd.read_csv('data/grids/grid_5500_epsg3857.csv')

CHANNELS = ["B4", "B3", "B2", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "AOT"]
MAX_RETRIES = 100

maus = gpd.read_file('data/maus/global_mining_polygons_v2.gpkg').to_crs(epsg=4326)

def process_tile(tile):
    gee_box = ee.geometry.Geometry.BBox(tile['min_lon'], tile['min_lat'], tile['max_lon'], tile['max_lat'])
    mid_lon = tile['max_lon'] + tile['min_lon'] / 2 
    mid_lat = tile['max_lat'] + tile['min_lat'] / 2
    img_string = f'data/images/{mid_lon:.6f}_{mid_lat:.6f}.tif'
    image = ee.imagecollection.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate('2019-01-01', '2020-01-01') \
        .filterBounds(gee_box) \
        .filter(ee.filter.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))\
        .select(CHANNELS)\
        .median()\
    
    params = {
        'scale': 10,
        'region': gee_box,
        'format': 'GeoTIFF'
    }

    url = image.getDownloadURL(params)
    
    tries = 0
    response = None
    while tries < MAX_RETRIES:
        try:
            response = requests.get(url)
            break
        except:
            tries += 1

    if not response:
        return

    with open(img_string, 'wb') as f:
        f.write(response.content)

    with rasterio.open(img_string) as src:
        meta = src.meta.copy()
        transform = src.transform
        width, height = src.width, src.height
        crs = src.crs
        bounds = src.bounds
        bands_data = src.read() 
        
    bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bounds)], crs=crs)
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
        'dtype': 'uint16'  # adjust if needed
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



tiles = [tile for _, tile in boxes.iterrows()]

results = []
with ProcessPoolExecutor() as executor:
    for result in tqdm(executor.map(process_tile, tiles), total=len(tiles)):
        results.append(result)


