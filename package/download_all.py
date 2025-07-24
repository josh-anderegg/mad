import ee
import pandas as pd
import requests
import rasterio
import geopandas as gpd
import os
import numpy as np
import json
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from shapely.geometry import box
from rasterio.features import rasterize
from tqdm import tqdm
from datetime import datetime
from package import BASE_DIR
DOWNLOAD_DIR = None
GRID_PATH = None
MAUS_PATH = None
ECOREGION_PATH = None
MAX_RETRIES = None


CHANNELS = [
    "TCI_R",
    "TCI_G",
    "TCI_B",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B8A",
    "B9",
    "B11",
    "B12",
    "AOT",
]

WORLD_COVER_MAP = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}

_maus, _regions = None, None


def load_data(maus_path, regions_path):
    global _maus, _regions
    if _maus is None:
        _maus = gpd.read_file(maus_path).to_crs(epsg=4326)
    if _regions is None:
        _regions = gpd.read_file(regions_path).to_crs(epsg=3857)
    return _maus, _regions


def download_all_parallel(DOWNLOAD_DIR, GRID_PATH, MAUS_PATH, ECOREGION_PATH, MAX_RETRIES):
    boxes = pd.read_csv(GRID_PATH)

    tiles = [tile for _, tile in boxes.iterrows()]

    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process_tile, tile, DOWNLOAD_DIR, MAUS_PATH, ECOREGION_PATH, MAX_RETRIES)
            for tile in tiles
        ]

        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            results.append(result)


def download_to(url, path, max_retries):
    tries = 0
    response = None
    while tries < max_retries:
        try:
            response = requests.get(url)
            with open(path, "wb") as f:
                f.write(response.content)
            return True
        except Exception:
            tries += 1
    return False


def get_biome(box, regions):
    intersecting = regions[regions.geometry.intersects(box)]
    if intersecting.empty:
        return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"

    # return intersecting.iloc[0]['BIOME_NAME'], intersecting.iloc[0]['ECO_NAME'f dn, intersecting.iloc[0]['BIOME_NUM'], intersecting.iloc[0]['OBJECTID']
    intersecting = intersecting.copy()
    intersecting["overlap_area"] = intersecting.geometry.intersection(box).area

    best_match = intersecting.loc[intersecting["overlap_area"].idxmax()]

    return (
        best_match["BIOME_NAME"],
        best_match["ECO_NAME"],
        best_match["BIOME_NUM"],
        best_match["OBJECTID"],
    )


def process_tile(tile, download_dir, MAUS_PATH, ECOREGION_PATH, max_retries):
    try:
        mid_lon = tile["max_lon"] + tile["min_lon"] / 2
        mid_lat = tile["max_lat"] + tile["min_lat"] / 2

        # Use hash to make reproducible
        id_string = hashlib.sha256(f"{mid_lon}/{mid_lat}".encode()).hexdigest()
        # Early stopping condition if already downloaded (NOTE: does not work if less that 5 images can be downloaded)
        if all([os.path.exists(f'{download_dir}/S2_{id_string}_{j}.tif') for j in range(5)]):
            return
        maus, regions = load_data(MAUS_PATH, ECOREGION_PATH)
        # maus = gpd.read_file(MAUS_PATH).to_crs(epsg=4326)
        # regions = gpd.read_file(ECOREGION_PATH).to_crs(crs=3857)

        gee_box = ee.geometry.Geometry.BBox(
            tile["min_lon"], tile["min_lat"], tile["max_lon"], tile["max_lat"]
        )

        temp_cov = BASE_DIR / f"data/temp/coverage_{id_string}.tif"
        coverage_image = (
            ee.imagecollection.ImageCollection("ESA/WorldCover/v100")
            .filterBounds(gee_box)
            .first()
        )

        images = (
            ee.imagecollection.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate("2019-01-01", "2020-01-01")
            .filterBounds(gee_box)
            .filter(ee.filter.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
            .limit(10)
            .select(CHANNELS)
            .toList(5)
        )

        params = {"scale": 10, "region": gee_box, "format": "GeoTIFF"}

        esa_url = coverage_image.getDownloadURL(params)
        success_cov = download_to(esa_url, temp_cov, max_retries)
        if not success_cov:
            print("Failed to download coverage image")

        with rasterio.open(temp_cov) as esa_src:
            esa_data = esa_src.read(1).astype("uint8")
            # unique_values, counts = np.unique(esa_data, return_counts=True)
            world_cover_histogram = {}

            for code, label in WORLD_COVER_MAP.items():
                count = int(np.sum(esa_data == code))
                world_cover_histogram[label] = count

        for i in range(images.size().getInfo()):
            img_string = f"{download_dir}/S2_{id_string}_{i}.tif"
            if os.path.exists(img_string):
                continue

            temp_sat = BASE_DIR / f"data/temp/satellite_{id_string}_{i}.tif"
            image = ee.image.Image(images.get(i)).reproject(crs="EPSG:3857", scale=10)
            url = image.getDownloadURL(params)
            success_sat = download_to(url, temp_sat, max_retries)

            unix_date = image.date().getInfo()["value"]  # type: ignore
            date = str(datetime.fromtimestamp(unix_date / 1000))
            if not success_sat:
                print("Failed to download satellite image")

            with rasterio.open(temp_sat) as src:
                meta = src.meta.copy()
                transform = src.transform
                width, height = src.width, src.height
                crs = src.crs
                bounds = src.bounds
                bands_data = src.read()

            bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bounds)], crs=crs)
            maus_proj = maus.to_crs(crs)
            bbox_gdf_proj = bbox_gdf.to_crs(crs)
            biome, ecoregion, biome_num, ecoregion_num = get_biome(box(*bounds), regions)
            gdf_in_tile = gpd.overlay(maus_proj, bbox_gdf_proj, how="intersection")
            shapes = (
                (geom, 1)
                for geom in gdf_in_tile.geometry
                if geom.is_valid and not geom.is_empty
            )

            mine_mask = rasterize(
                shapes=shapes,
                out_shape=(height, width),
                transform=transform,
                fill=0,
                dtype="uint8",
            )

            meta.update({"count": bands_data.shape[0] + 1, "dtype": "uint16"})

            with rasterio.open(img_string, "w", **meta) as dst:
                for j in range(bands_data.shape[0]):
                    dst.write(bands_data[j], j + 1)

                dst.write(mine_mask, bands_data.shape[0] + 1)
                dst.set_band_description(1, "TCI_R: (True color red)")
                dst.set_band_description(2, "TCI_G: (True color green)")
                dst.set_band_description(3, "TCI_B: (True color blue)")
                dst.set_band_description(4, "B4: (Red)")
                dst.set_band_description(5, "B3: (Green)")
                dst.set_band_description(6, "B2: (Blue)")
                dst.set_band_description(7, "B5: (Red Edge 1)")
                dst.set_band_description(8, "B6: (Red Edge 2)")
                dst.set_band_description(9, "B7: (Red Edge 3)")
                dst.set_band_description(10, "B8: (Near Infrared)")
                dst.set_band_description(11, "B8A: (Narrow Near Infrared)")
                dst.set_band_description(12, "B9: (Water vapor)")
                dst.set_band_description(13, "B11: (SWIR 1)")
                dst.set_band_description(14, "B12: (SWIR 2)")
                dst.set_band_description(15, "AOT: (Aerorosol Optical Thickness)")
                dst.set_band_description(16, "Mine: (MAUS mining asset)")
                dst.update_tags(WORLD_COVER=json.dumps(world_cover_histogram))
                dst.update_tags(DATE=date)
                dst.update_tags(BIOME=biome)
                dst.update_tags(ECOREGION=ecoregion)
                dst.update_tags(BIOME_NUM=biome_num)
                dst.update_tags(ECOREGION_NUM=ecoregion_num)

            os.remove(temp_sat)
        os.remove(temp_cov)
    except Exception as e:
        with open('output.txt', 'a') as f:
            f.write(f"failure happened {e}\n")
        pass


def parse_args(args):
    global DOWNLOAD_DIR, GRID_PATH, MAUS_PATH, ECOREGION_PATH, MAX_RETRIES
    DOWNLOAD_DIR = args.download_dir
    GRID_PATH = args.grid_path
    MAUS_PATH = args.maus
    ECOREGION_PATH = args.ecoregion
    MAX_RETRIES = 1000


def run(args):
    # GEE authentication
    ee.Authenticate()
    ee.Initialize(project="siam-josh")

    download_all_parallel(DOWNLOAD_DIR, GRID_PATH, MAUS_PATH, ECOREGION_PATH, MAX_RETRIES)
