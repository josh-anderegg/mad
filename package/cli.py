import argparse
import package.lasso_train


def main():
    parser = argparse.ArgumentParser("MAD CLI interface")

    subparses = parser.add_subparsers(dest="action", required=True)

    lasso_parser = subparses.add_parser("lasso", help="Lasso analysis operations")
    lasso_subparsers = lasso_parser.add_subparsers(dest="command", required=True)

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

    # yolo_parser = subparses.add_parser("yolo", help="YOLO analysis operations")
    # yolo_subparsers = yolo_parser.add_subparsers(dest="command", required=True)

    args = parser.parse_args()
    match (args.action, args.command):
        case ("lasso", "train"):
            package.lasso_train.run(args)
        case ("lasso", "predict"):
            package.lasso_predict.run(args)
        # case ("yolo", "train"):
