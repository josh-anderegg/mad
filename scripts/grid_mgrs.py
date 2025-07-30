import geopandas as gpd
from shapely import Polygon
from mgrs import MGRS

m = MGRS()

# Load your polygons
maus = gpd.read_file("../data/maus/global_mining_polygons_v2.gpkg")  # or shapefile

tiles = set()
for polygon in maus['geometry']:
    try:
        polygon_center = Polygon(polygon).centroid

        mgrs_polygon_center = m.toMGRS(polygon_center.y, polygon_center.x)
        tiles.add(mgrs_polygon_center[:5])
    except:
        pass

with open("tiles.txt", "w") as f:
    f.write("\n".join(tiles))
