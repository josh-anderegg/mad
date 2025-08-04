import rasterio
import geopandas as gpd
import os
import numpy as np
import random
from shapely.geometry import box
from shapely.affinity import rotate
from PIL import Image, ImageDraw, ImageOps
import cv2

# Paths
tif_path = "../data/s3-images/10SFJ.tif"
polygon_path = "../data/maus/global_mining_polygons_v2.gpkg"
output_path = "full_overlay.jpg"

# Load raster and image bands
src = rasterio.open(tif_path)
bands = src.read([1, 2, 3]).astype(np.float32)


def normalize_band(band):
    p2 = np.percentile(band, 2)
    p98 = np.percentile(band, 98)
    band = np.clip((band - p2) / (p98 - p2), 0, 1)
    return (band * 255).astype(np.uint8)


bands = np.array([normalize_band(b) for b in bands])
image = np.moveaxis(bands, 0, -1)
image = np.moveaxis(bands, 0, -1)
image = np.clip(image, 0, 255).astype(np.uint8)
pil_image = Image.fromarray(image)
draw = ImageDraw.Draw(pil_image)

# Load mining polygons in the same CRS
gdf = gpd.read_file(polygon_path).to_crs(src.crs)

# Parameters
num_snippets = 50
size = 640
intersect_target = int(num_snippets * 0.7)
nonintersect_target = num_snippets - intersect_target
intersect_count = 0
nonintersect_count = 0
image_np = np.array(pil_image)

snapshot_dir = "snapshots"
os.makedirs(snapshot_dir, exist_ok=True)
snapshot_id = 0
# Generate and draw
height, width = image.shape[:2]
colormap = {"intersect": "red", "nonintersect": "blue"}
attempts = 0


def order_points_clockwise(pts):
    # Order points: top-left, top-right, bottom-right, bottom-left
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect


def crop_rotated_region(img_np, square_pix, angle, out_size):
    # Get polygon coordinates (drop closing point)
    coords = np.array(square_pix.exterior.coords[:-1], dtype=np.float32)

    if len(coords) != 4:
        raise ValueError("Expected 4 points for rotated square, got %d" % len(coords))

    src_pts = order_points_clockwise(coords)
    dst_pts = np.array([
        [0, 0],
        [out_size - 1, 0],
        [out_size - 1, out_size - 1],
        [0, out_size - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(img_np, M, (out_size, out_size))
    return warped


def random_square(img_w, img_h, size, angle):
    size = random.randint(640, 3200)
    x = random.randint(0, img_w - size)
    y = random.randint(0, img_h - size)
    square = box(x, y, x + size, y + size)
    square = rotate(square, angle, origin="center", use_radians=False)
    return square, (x, y)


while (intersect_count + nonintersect_count) < num_snippets and attempts < 1000:
    attempts += 1
    angle = random.uniform(0, 360)
    square_pix, _ = random_square(width, height, size, angle)

    # Convert pixel-space polygon to geo-coordinates
    coords = [(int(pt[0]), int(pt[1])) for pt in np.array(square_pix.exterior.coords)]
    geo_coords = [src.transform * pt for pt in coords]
    poly = gpd.GeoSeries(
        [box(*np.array(geo_coords).T.min(axis=1), *np.array(geo_coords).T.max(axis=1))],
        crs=src.crs,
    )

    intersects = gdf.intersects(poly[0]).any()

    if intersects and intersect_count >= intersect_target:
        continue
    if not intersects and nonintersect_count >= nonintersect_target:
        continue

    # Draw square on image
    draw.polygon(
        coords,
        outline=colormap["intersect" if intersects else "nonintersect"],
        width=10,
    )

    # Update counts
    if intersects:
        intersect_count += 1
    else:
        nonintersect_count += 1
    snapshot = crop_rotated_region(image_np, square_pix, angle, size)

    # Save upright patch
    snapshot_path = os.path.join(
        snapshot_dir,
        f"{'intersect' if intersects else 'nonintersect'}_{snapshot_id}.jpg",
    )
    Image.fromarray(snapshot).save(snapshot_path)
    snapshot_id += 1

pil_image.save(output_path)
print(f"Overlay saved to {output_path}")
