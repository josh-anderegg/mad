import geopandas as gpd

# Read the Sentinel-2 tile grid (KML or KMZ)
tiles_gdf = gpd.read_file("../data/grids/S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml")
maus = gpd.read_file("../data/maus/global_mining_polygons_v2.gpkg")  # or shapefile

intersections = gpd.sjoin(tiles_gdf, maus, how="inner", predicate="intersects")
for _, row in intersections.iterrows():
    print(row['geometry'].bounds, row['Name'])
tile_names = intersections['Name'].unique()
geometries = [", ".join(map(str, row['geometry'].bounds)) for idx, row in intersections.iterrows()]
geometries = set(geometries)
found = 0
total = len(tile_names)
with open("tiles.txt", "w") as f:
    f.write("\n".join(tile_names))
with open("bboxes.txt", "w") as f:
    f.write("\n".join(geometries))
