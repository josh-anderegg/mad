import os
import shutil
import rasterio
IMAGE_PATH = 'data/images/'
CLUSTER_PATH = 'data/clusters/'

shutil.rmtree(CLUSTER_PATH)
os.makedirs(CLUSTER_PATH, exist_ok=True)

image_list = os.listdir(IMAGE_PATH)

for image in os.listdir(IMAGE_PATH):
    abs_path = IMAGE_PATH + image

    with rasterio.open(abs_path) as src:
        metadata = src.tags()
        biome = metadata['BIOME'].lower()
    biome = biome.replace(' ', '_')
    biome = biome.replace('/', '_')
    biome = biome.replace(',', '')
    biome = biome.replace('&', '')
    biome = biome.replace('__', '_')
    with open(CLUSTER_PATH + biome+'.txt', 'a') as file:
        file.write(IMAGE_PATH+image+'\n')

