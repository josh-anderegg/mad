import geopandas as gpd
from shapely import wkt

# --- Step 1: Read MGRS KML file ---
tiles = gpd.read_file("data/grids/S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml", driver="KML")

# Sometimes "description" holds WKT strings; if so, parse them:
# Example: extract LL_WKT field if direct load fails
if "LL_WKT" in tiles.columns:
    tiles["geometry"] = tiles["LL_WKT"].apply(wkt.loads)
    tiles = gpd.GeoDataFrame(tiles, geometry="geometry", crs="EPSG:4326")

# --- Step 2: Get Australia polygon ---
world = gpd.read_file("data/grids/ne_110m_admin_0_countries.shp")
australia = world[world["ADMIN"] == "Kenya"]

# --- Step 3: Make sure CRS matches ---
tiles = tiles.to_crs(australia.crs)

# --- Step 4: Spatial intersection ---
intersecting = gpd.sjoin(tiles, australia, how="inner", predicate="intersects")

# --- Step 5: Output ---
tile_ids = intersecting["Name"].to_list()

# Write to txt, one per line
with open("all_kenya.txt", "w") as f:
    f.write("\n".join(tile_ids))

