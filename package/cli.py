import argparse
from package import lasso_train, lasso_predict, create_grid, download_all, setup, create_dataset, create_database
from package import BASE_DIR

CHANNELS = [
    "TCI_R",
    "TCI_G",
    "TCI_B",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B8A",
    "B9",
    "B11",
    "B12",
    "AOT",
]


def main():
    parser = argparse.ArgumentParser("MAD CLI interface")

    subparsers = parser.add_subparsers(dest="action", required=True)

    lasso_parser = subparsers.add_parser("lasso", help="Lasso analysis operations")
    lasso_subparsers = lasso_parser.add_subparsers(dest="command", required=True)

    database_parser = subparsers.add_parser("database", help="Database operations")
    database_subparsers = database_parser.add_subparsers(dest="command", required=True)

    yolo_parser = subparsers.add_parser("yolo", help="YOLO operations")
    yolo_subparsers = yolo_parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Setup to run mad")
    setup_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose installation")
    setup_parser.add_argument("-m", "--minimal", action="store_true", help="Only create file structure, no downloads")

    lasso_train_parser = lasso_subparsers.add_parser("train", help="Train a lasso model")
    lasso_train_parser.add_argument("images", nargs="+", help="Path to tif file or files")
    lasso_train_parser.add_argument("output", type=str, help="Path the output directory for the graphs")
    lasso_train_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    lasso_train_parser.add_argument("-l", "--lambda-count", type=int, default=25, help="Amount of Lambdas iterated over (default: 10)")
    lasso_train_parser.add_argument("-m", "--minimal-lambda", type=int, default=-4, help="Minimal lambda used (10^-m) (default: -4)")
    lasso_train_parser.add_argument("-g", "--generate-output", default=True, action="store_false", help="Set if you want the script to create output")
    lasso_train_parser.add_argument("-c", "--count", type=int, default=10, help="Set the amount of images that should be used (default: 10)")
    lasso_train_parser.add_argument("-r", "--random-seed", type=str, default=None, help="Random string used for all the randomization done.")
    lasso_train_parser.add_argument("-p", "--pixel-count", type=int, default=1000, help="Maximal pixel count per image that is used to perform the lasso (default: 1000)")
    lasso_train_parser.add_argument("--pixel-ratios", type=str, default='0.5, 0.1, 0.4', help="Ratio between pixels taken inside, on the border and outside of the ground truth (default: 0.5, 0.1, 0.4)")
    lasso_train_parser.add_argument("-s", "--sigma", type=float, default=5, help="Sigma used to blur the ground truth. (default: 5)")
    lasso_train_parser.add_argument("--train-percentage", type=float, default=0.8, help="Percentage of the images that are used for the training vs. testing (default: 0.8)")
    lasso_train_parser.add_argument("-e", "--extend", action="store_true", default=False, help="Extends the values with Spectracl indices (default: False)")
    lasso_train_parser.add_argument("--super-extend", action="store_true", default=False, help="Extends the values with all possible Spectracl indices (default: False)")

    lasso_predict_parser = lasso_subparsers.add_parser("predict", help="Predict with a lasso model.")
    lasso_predict_parser.add_argument("images", nargs="+", help="Path to tif file or files.")
    lasso_predict_parser.add_argument("path", help="Path to the folder for which to perform the test.")
    lasso_predict_parser.add_argument("-s", "--sigma", type=float, default=5, help="Sigma used to blur the ground truth. (default: 5)")
    lasso_predict_parser.add_argument("-e", "--extend", action="store_true", default=False, help="Extends the values with Spectracl indices (default: False)")
    lasso_predict_parser.add_argument("--super-extend", action="store_true", default=False, help="Extends the values with all possible Spectracl indices (default: False)")

    database_create_parser = database_subparsers.add_parser("create", help="Create a database")
    database_create_parser.add_argument("name", type=str, help="Define the name of the database")
    database_create_parser.add_argument("source", type=str, help="Give a path to a polygonal .gpkg or the name of a country")
    database_create_parser.add_argument("-t", "--train-val-test-split", type=str, default='0.8, 0.1, 0.1', help="Ratios for the train, validation and test set in the format x, y ,z (default: 0.8, 0.1, 0.1)")
    database_create_parser.add_argument("-d", "--datapath", type=str, default=BASE_DIR / 'data', help="Path to the data directory")
    database_create_parser.add_argument("-r", "--random-seed", type=str, default=None, help="Random string used for all the randomization done.")

    database_download_parser = database_subparsers.add_parser("download", help="Download the provided grid")
    database_download_parser.add_argument("grid_path", help="Path to the grid to be downloaded.")
    database_download_parser.add_argument("download_dir", help="Path to the download directory")
    database_download_parser.add_argument("--bands", "-b", nargs="+", choices=CHANNELS, default=CHANNELS, help="List of band names")
    database_download_parser.add_argument("--maus", "-m", default=BASE_DIR / "data/maus/global_mining_polygons_v2.gpkg", help="Path to the maus .gpkg",)
    database_download_parser.add_argument("--ecoregion", "-e", default=BASE_DIR / "data/Ecoregions2017/Ecoregions2017.shp", help="Path to the maus .gpkg",)

    yolo_create_parser = yolo_subparsers.add_parser("create", help="Create a yolo dataset")
    yolo_create_parser.add_argument("database", help="Path to the .tif images to use")
    yolo_create_parser.add_argument("path", help="Output path to the final dataset")
    yolo_create_parser.add_argument("--maus", "-m", default=BASE_DIR / 'data/maus/global_mining_polygons_v2.gpkg', help="Path to the maus .gpkg set")
    yolo_create_parser.add_argument("--random-seed", "-s", help="Random seed for the split")
    yolo_create_parser.add_argument("--filters", "-f", default=[], nargs="+", help="Filters to apply")
    yolo_create_parser.add_argument("--expansions", "-e", default=[], nargs="+", help="Expansions to apply")

    args = parser.parse_args()
    action = args.action
    command = getattr(args, "command", None)
    match (action, command):
        case ("setup", None):
            setup.run(args)
        case ("lasso", "train"):
            lasso_train.run(args)
        case ("lasso", "predict"):
            lasso_predict.run(args)
        case ("database", "create"):
            create_database.run(args)
        case ("database", "download"):
            download_all.run(args)
        case ("yolo", "create"):
            create_dataset.run(args)
