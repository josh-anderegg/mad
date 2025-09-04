from package import BASE_DIR
from pathlib import Path
from ultralytics import YOLO
import os, glob
from shapely.ops import transform
import rasterio
from shapely.geometry import Point, box
import geopandas as gpd
import pyproj

DATASET_PATH = None
OUTPUT_PATH = None
MODEL_PATH = None


def parse_args(args):
    global DATASET_PATH, OUTPUT_PATH, MODEL_PATH
    DATASET_PATH = args.dataset
    OUTPUT_PATH = args.output
    if OUTPUT_PATH is None:
        path = Path(DATASET_PATH)
        OUTPUT_PATH = BASE_DIR / f"outputs/{path.name}"
    MODEL_PATH = args.model


def perform_prediction():
    global MODEL_PATH, DATASET_PATH
    model = YOLO(MODEL_PATH)

    test_folder = Path(DATASET_PATH) / "test"

    if not test_folder.exists():
        raise FileNotFoundError(f"Test folder not found: {test_folder}")

    model.predict(
        source=test_folder,
        save=True,
        project=OUTPUT_PATH,
        name="predictions",
        exist_ok=True,
        imgsz=640
    )


def generate_geolocations():
    target_crs = "EPSG:3857"

    output_gpkg_boxes = f"{OUTPUT_PATH}/prediction.gpkg"
    image_folder = f"{OUTPUT_PATH}/predictions"
    layer_name = "Predictions"
    box_features = []

    image_count = len(glob.glob(os.path.join(image_folder, "*.jpg")))
    i = 0
    for img_path in glob.glob(os.path.join(image_folder, "*.jpg")):
        i += 1
        print(f"{i}/{image_count}")
        base = os.path.splitext(os.path.basename(img_path))[0]
        txt_path = os.path.join(image_folder, base + ".txt")

        if not os.path.exists(txt_path):
            continue

        with rasterio.open(img_path) as src:
            bounds = src.bounds
            left, bottom, right, top = bounds
            width_geo = right - left
            height_geo = top - bottom
            src_crs = src.crs
            transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)
            with open(txt_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue

                    class_id, x_c_rel, y_c_rel, w_rel, h_rel = map(float, parts)
                    class_id = int(class_id)

                    x_c_geo = left + x_c_rel * width_geo
                    y_c_geo = (
                        top - y_c_rel * height_geo
                    )

                    w_geo = w_rel * width_geo
                    h_geo = h_rel * height_geo

                    x_min_geo = x_c_geo - w_geo / 2
                    x_max_geo = x_c_geo + w_geo / 2
                    y_min_geo = y_c_geo - h_geo / 2
                    y_max_geo = y_c_geo + h_geo / 2
                    polygon = box(x_min_geo, y_min_geo, x_max_geo, y_max_geo)
                    polygon_proj = transform(transformer.transform, polygon)
                    box_features.append(
                        {
                            "geometry": polygon_proj,
                            "class_id": class_id,
                            "image": base + ".jpg",
                        }
                    )

            if not box_features:
                return

    gdf_boxes = gpd.GeoDataFrame(box_features, crs=3857)
    gdf_boxes.to_file(output_gpkg_boxes, layer=layer_name, driver="GPKG")


def run(args):
    parse_args(args)
    perform_prediction()
    generate_geolocations()
