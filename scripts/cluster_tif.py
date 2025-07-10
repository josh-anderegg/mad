from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import rasterio
from pathlib import Path
from tqdm import tqdm

# Script to cluster the images according to their respective biomes
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = BASE_DIR / 'data/images'
CLUSTER_PATH = BASE_DIR / 'data/clusters'

shutil.rmtree(CLUSTER_PATH)
os.makedirs(CLUSTER_PATH, exist_ok=True)
image_list = os.listdir(IMAGE_PATH)

def process_image(image):
    abs_path = IMAGE_PATH / image
    with rasterio.open(abs_path) as src:
        metadata = src.tags()
        biome = metadata['BIOME'].lower()
    biome = biome.replace(' ', '_')
    biome = biome.replace('/', '_')
    biome = biome.replace(',', '')
    biome = biome.replace('&', '')
    biome = biome.replace('__', '_')
    with open(CLUSTER_PATH / f"{biome}.txt", 'a') as file:
        file.write(str(IMAGE_PATH / image) + '\n')

with ThreadPoolExecutor() as executor:
    list(tqdm(executor.map(process_image, image_list), total=len(image_list), desc=f"Processing images into clusters"))
