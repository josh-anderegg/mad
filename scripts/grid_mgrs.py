import geopandas as gpd
import requests

# Read the Sentinel-2 tile grid (KML or KMZ)
tiles_gdf = gpd.read_file("~/Downloads/S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml")
maus = gpd.read_file("../data/maus/global_mining_polygons_v2.gpkg")  # or shapefile

intersections = gpd.sjoin(tiles_gdf, maus, how="inner", predicate="intersects")
tile_names = intersections['Name'].unique()

found = 0
total = len(tile_names)
# tiles = []
# for coords in tile_names:
#     fst, snd, lst = int(coords[:2]), coords[2], coords[3:]
#     found = False
#     for i in range(1, 12):
#         for j in range(1, 31):
#             metadata_link = f"https://sentinel-s2-l2a.s3.amazonaws.com/tiles/{fst}/{snd}/{lst}/2019/{i}/{j}/0/metadata.xml"
#             response = requests.head(metadata_link, allow_redirects=True, timeout=10)
#
#             if response.status_code == 200:
#                 found += 1
#                 tiles.append(coords)
#                 found = True
#                 break
#         if found:
#             break
#     if not found:
#         print(f"{coords} could no be found")
#     else:
#         print(f"{coords} found")
with open("tiles.txt", "w") as f:
    f.write("\n".join(tile_names))
