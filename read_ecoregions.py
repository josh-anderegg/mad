import geopandas as gpd
import matplotlib.pyplot as plt

# Load the shapefile
regions = gpd.read_file("data/Ecoregions2017/Ecoregions2017.shp").to_crs(crs=3857)
maus = gpd.read_file("data/maus/Global_Mining_Polygons_v2.shp").to_crs(crs=3857)


if regions.crs != maus.crs:
    maus = maus.to_crs(regions.crs) # type: ignore

for idx, mining_poly in maus.iterrows():
    intersecting = regions[regions.geometry.intersects(mining_poly.geometry)]
    
    if intersecting.empty:
        print("Unexpectedly no biome intersections")
        continue
    
    if len(intersecting) == 1:
        print(intersecting.iloc[0]['BIOME_NAME'], intersecting.iloc[0]['ECO_NAME'])
        continue
    
    print("Multiple matches")
    intersecting = intersecting.copy()
    intersecting["overlap_area"] = intersecting.geometry.intersection(mining_poly.geometry).area

    best_match = intersecting.loc[intersecting["overlap_area"].idxmax()]
    print(best_match['BIOME_NAME'], best_match['ECO_NAME'])
    

