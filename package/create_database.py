from package import BASE_DIR, random_seed
import os
import geopandas as gpd
import random
DATABASE_PATH = None
INTERSECTION = None
SPLIT = None
SEED = None


def create_split(tile_names):
    global SPLIT
    train_perc, val_perc, test_perc = SPLIT
    total = len(tile_names)
    random.shuffle(tile_names)
    thresh1 = int(total * train_perc)
    thresh2 = int(total * (train_perc + val_perc))
    return tile_names[:thresh1], tile_names[thresh1:thresh2], tile_names[thresh2:]


def get_intersection():
    global INTERSECTION
    try:
        aws_tiles = gpd.read_file(BASE_DIR / "data/grids/S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml")
    except FileNotFoundError:
        print("The mgrs sentinel grid was not found, did you run `mad setup`?")

    if INTERSECTION.endswith(".gpkg"):
        polygons = gpd.read_file(INTERSECTION)
    else:
        try:
            polygons = gpd.read_file(BASE_DIR / "data/grids/ne_110m_admin_0_countries.shp")
        except FileNotFoundError:
            print("The country polygons were not found, did you run `mad setup`?")

        try:
            polygons = polygons[polygons["ADMIN"] == INTERSECTION]
        except Exception:
            print("Country name seems invalid!")

    intersections = gpd.sjoin(aws_tiles, polygons, how="inner", predicate="intersects")
    tile_names = intersections['Name'].unique()
    return tile_names


def parse_args(args):
    global DATABASE_PATH, SPLIT, INTERSECTION, SEED
    DATABASE_PATH = f"{args.datapath}/{args.name}"
    if os.path.exists(DATABASE_PATH):
        raise FileExistsError(f"{args.name} is already used under {DATABASE_PATH}, choose a new one!")

    SPLIT = list(map(float, args.train_val_test_split.split(",")[:3]))
    if not abs(sum(SPLIT) - 1.0) < 1e-6:
        raise ValueError("Split ratios must sum to 1.0")

    INTERSECTION = args.source
    if args.random_seed is None:
        SEED = random_seed()
    else:
        SEED = args.random_seed
    random.seed(SEED)


def write_files(tile_names, train, validation, test):
    global DATABASE_PATH, SEED
    os.makedirs(DATABASE_PATH, exist_ok=False)

    with open(f"{DATABASE_PATH}/tiles.txt", "w") as f:
        f.write("\n".join(tile_names))
    with open(f"{DATABASE_PATH}/train.txt", "w") as f:
        f.write("\n".join(train))
    with open(f"{DATABASE_PATH}/val.txt", "w") as f:
        f.write("\n".join(validation))
    with open(f"{DATABASE_PATH}/test.txt", "w") as f:
        f.write("\n".join(test))
    with open(f"{DATABASE_PATH}/seed.txt", "w") as f:
        f.write(SEED)


def run(args):
    parse_args(args)
    tile_names = get_intersection()
    train, validation, test = create_split(tile_names)
    write_files(tile_names, train, validation, test)
