import rasterio
import geopandas as gpd
import random
from shapely.geometry import box
import numpy as np
from PIL import Image
import os

STRETCH_MIN = 500
STRETCH_MAX = 3500


def generate_tiles_and_labels(
    tif_path, output_img_dir, output_lbl_dir, maus_df, tile_size=620
):
    try:
        os.makedirs(output_img_dir, exist_ok=True)
        os.makedirs(output_lbl_dir, exist_ok=True)

        with rasterio.open(tif_path) as src:
            rgb = src.read([1, 2, 3])  # Sentinel-2 Red, Green, Blue
            transform = src.transform
            raster_crs = src.crs
            height, width = rgb.shape[1:]

            # Reproject and spatial index for performance
            gdf_proj = maus_df.to_crs(raster_crs)
            sindex = gdf_proj.sindex

            tile_id = 0
            for y in range(0, height, tile_size):
                for x in range(0, width, tile_size):
                    if y + tile_size > height or x + tile_size > width:
                        continue  # skip incomplete tiles

                    # Extract tile
                    tile = rgb[:, y : y + tile_size, x : x + tile_size].astype(
                        np.float32
                    )
                    tile_img = np.transpose(tile, (1, 2, 0))
                    tile_img = (
                        np.clip(
                            (tile_img - STRETCH_MIN) / (STRETCH_MAX - STRETCH_MIN), 0, 1
                        )
                        * 255
                    )
                    tile_img = tile_img.astype(np.uint8)

                    # Save tile image
                    tile_name = f"tile_{tile_id:04d}"
                    img_path = os.path.join(output_img_dir, f"{tile_name}.jpg")
                    Image.fromarray(tile_img).save(img_path)

                    # Geospatial bounds of tile
                    ulx, uly = rasterio.transform.xy(transform, y, x, offset="ul")
                    lrx, lry = rasterio.transform.xy(
                        transform, y + tile_size, x + tile_size, offset="lr"
                    )
                    tile_bounds = box(ulx, lry, lrx, uly)

                    # Find intersecting polygons
                    hits_idx = list(sindex.intersection(tile_bounds.bounds))
                    hits = gdf_proj.iloc[hits_idx]

                    labels = []
                    for _, row in hits.iterrows():
                        poly = row.geometry
                        if not poly.intersects(tile_bounds):
                            continue
                        inter = poly.intersection(tile_bounds)
                        if inter.is_empty:
                            continue

                        # Intersection bounding box
                        minx, miny, maxx, maxy = inter.bounds
                        center_x = (minx + maxx) / 2
                        center_y = (miny + maxy) / 2

                        # Convert to pixel relative to tile
                        pixel_cx, pixel_cy = ~transform * (center_x, center_y)
                        pixel_w1, _ = ~transform * (minx, 0)
                        pixel_w2, _ = ~transform * (maxx, 0)
                        _, pixel_h1 = ~transform * (0, miny)
                        _, pixel_h2 = ~transform * (0, maxy)

                        # Relative to tile's top-left
                        rel_cx = (pixel_cx - x) / tile_size
                        rel_cy = (pixel_cy - y) / tile_size
                        rel_w = (pixel_w2 - pixel_w1) / tile_size
                        rel_h = (pixel_h2 - pixel_h1) / tile_size

                        if 0 <= rel_cx <= 1 and 0 <= rel_cy <= 1:
                            labels.append(
                                f"0 {rel_cx:.6f} {rel_cy:.6f} {rel_w:.6f} {rel_h:.6f}"
                            )

                    # Save labels
                    lbl_path = os.path.join(output_lbl_dir, f"{tile_name}.txt")
                    with open(lbl_path, "w") as f:
                        f.write("\n".join(labels))

                    tile_id += 1
        print("Succeeded for", tif_path)
    except:
        print("failed for ", tif_path)


all_tif_path = "/run/media/cynik/Elements/s2-images/"
maus_df = gpd.read_file("~/Documents/mad/data/geometries/global_mining_polygons_v2.gpkg")
all_tifs = [path for path in os.listdir(all_tif_path) if path.lower().endswith(".tif")]
length = len(all_tifs)
random.shuffle(all_tifs)
thresh1 = int(length * 0.7)
thresh2 = int(length * 0.9)

train_tifs = all_tifs[:thresh1]
validation_tifs = all_tifs[thresh1:thresh2]
test_tifs = all_tifs[thresh2:]

for tif in train_tifs:
    generate_tiles_and_labels(
        all_tif_path + tif,
        "~/Documents/mad/data/yolo00/images/train/",
        "~/Documents/mad/data/yolo00/labels/train/",
        maus_df,
        tile_size=620,
    )
for tif in validation_tifs:
    generate_tiles_and_labels(
        all_tif_path + tif,
        "~/Documents/mad/data/yolo00/images/val/",
        "~/Documents/mad/data/yolo00/labels/val/",
        maus_df,
        tile_size=620,
    )
for tif in test_tifs:
    generate_tiles_and_labels(
        all_tif_path + tif,
        "~/Documents/mad/data/yolo00/images/test/",
        "~/Documents/mad/data/yolo00/labels/test/",
        maus_df,
        tile_size=620,
    )
