#!/usr/bin/python python
import os, glob
from shapely.ops import transform
import rasterio
from shapely.geometry import Point, box
import geopandas as gpd
import pyproj
target_crs = "EPSG:3857"


def yolo_folder_to_geopkg(
    image_folder,
    output_gpkg_boxes,
    output_gpkg_centers,
    layer_name="detections",
    layer_name_centers="centers",
):
    box_features = []
    center_features = []
    l = len(glob.glob(os.path.join(image_folder, "*.jpg")))
    i = 0
    for img_path in glob.glob(os.path.join(image_folder, "*.jpg")):
        i += 1
        print(f"{i}/{l}")
        base = os.path.splitext(os.path.basename(img_path))[0]
        txt_path = os.path.join(image_folder, base + ".txt")

        if not os.path.exists(txt_path):
            continue

        with rasterio.open(img_path) as src:
            bounds = src.bounds  # left, bottom, right, top in CRS
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

                    # YOLO relative -> georeferenced coordinates
                    x_c_geo = left + x_c_rel * width_geo
                    y_c_geo = (
                        top - y_c_rel * height_geo
                    )  # invert y because YOLO uses top-left origin

                    w_geo = w_rel * width_geo
                    h_geo = h_rel * height_geo

                    # Bounding box
                    x_min_geo = x_c_geo - w_geo / 2
                    x_max_geo = x_c_geo + w_geo / 2
                    y_min_geo = y_c_geo - h_geo / 2
                    y_max_geo = y_c_geo + h_geo / 2
                    polygon = box(x_min_geo, y_min_geo, x_max_geo, y_max_geo)
                    point = Point(x_c_geo, y_c_geo)
                    polygon_proj = transform(transformer.transform, polygon)
                    point_proj = transform(transformer.transform, point)
                    box_features.append(
                        {
                            "geometry": polygon_proj,
                            "class_id": class_id,
                            "image": base + ".jpg",
                        }
                    )

                    # Center point
                    center_features.append(
                        {
                            "geometry": point_proj,
                            "class_id": class_id,
                            "image": base + ".jpg",
                        }
                    )

            if not box_features:
                return

    # Save bounding boxes
    gdf_boxes = gpd.GeoDataFrame(box_features, crs=3857)
    gdf_boxes.to_file(output_gpkg_boxes, layer=layer_name, driver="GPKG")

    # Save center points
    gdf_centers = gpd.GeoDataFrame(center_features, crs=3857)
    gdf_centers.to_file(output_gpkg_centers, layer=layer_name_centers, driver="GPKG")

    print(f"✅ Exported {len(box_features)} boxes to {output_gpkg_boxes}")
    print(f"✅ Exported {len(center_features)} centers to {output_gpkg_centers}")


yolo_folder_to_geopkg(
    "outputs/australia-negatives/test_predictions/",
    "test.gpkg",
    "center.gpkg",
    layer_name="detections",
)
