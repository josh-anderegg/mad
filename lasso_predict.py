#!/usr/bin/env python3

import joblib
import argparse
import json

from warnings import simplefilter
import numpy as np

from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tif_utils import tif_to_vec, output_prediction, extend
simplefilter("ignore", category=ConvergenceWarning)

parser = argparse.ArgumentParser()

parser.add_argument("path", help="Path to the folder for which to perform the test.")
parser.add_argument("images", nargs="+" , help="Path to tif file or files.")
parser.add_argument("-s", "--sigma", type=float, default=5 , help="Sigma used to blur the ground truth. (default: 5)")
parser.add_argument("-e", "--extend", action="store_true", default=False, help="Extends the values with Spectracl indices (default: False)")

args = parser.parse_args()
SIGMA = args.sigma
EXTEND = args.extend


PATH = args.path
IMAGES = args.images
lasso = joblib.load(f'{PATH}/model.pkl')
results = {}
for image in IMAGES:
    X, y = tif_to_vec(image, 0, 0, 0, SIGMA, False)
    if EXTEND:
        X = extend(X)
    y_pred = lasso.predict(X)
    output_prediction(y_pred, image, PATH + '/test_images')
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



