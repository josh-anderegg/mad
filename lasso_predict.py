#!/usr/bin/env python3

import joblib
import argparse
import json

from warnings import simplefilter
import numpy as np

from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tif_utils import tif_to_vec, output_prediction
simplefilter("ignore", category=ConvergenceWarning)

parser = argparse.ArgumentParser()

parser.add_argument("path", help="Path to the folder for which to perform the test.")
parser.add_argument("images", nargs="+" , help="Path to tif file or files.")
parser.add_argument("-p", "--pixel-count", type=int, default=1000 , help="Maximal pixel count per image that is used to perform the lasso (default: 1000)")
parser.add_argument("--pixel-ratios", type=str, default='0.5, 0.1, 0.4' , help="Ratio between pixels taken inside, on the border and outside of the ground truth (default: 0.5, 0.1, 0.4)")
parser.add_argument("-s", "--sigma", type=float, default=5 , help="Sigma used to blur the ground truth. (default: 5)")
args = parser.parse_args()
PIXEL_PER_IMAGE = args.pixel_count
SIGMA = args.sigma
try:
    IN, EDGE, OUT = map(float, args.pixel_ratios.split(','))
    if not abs(IN + EDGE + OUT - 1.0) < 1e-6:
        raise ValueError("Split ratios must sum to 1.0")
except:
    raise ValueError(f"Could not parse in split values: {args.pixel_ratios}, should be of the form IN, EDGE, OUT. All of them being floats.")

PATH = args.path
lasso = joblib.load(f'{PATH}/model.pkl')
results = {}
for image in args.images:
    X, y = tif_to_vec(image, IN, EDGE, PIXEL_PER_IMAGE, SIGMA, False)
    y_pred = lasso.predict(X)
    output_prediction(y_pred, image, PATH)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)

    results['image'] = {
        'MSE': mse,
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2,
    }

with open(f'{PATH}/train.json', 'w') as f:
    json.dump(results, f, indent=4)



