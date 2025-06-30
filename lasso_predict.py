#!/usr/bin/env python3

import joblib
import argparse
import json

from warnings import simplefilter
import numpy as np

from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tif_utils import tif_to_vec, output_prediction, extend, super_extend
simplefilter("ignore", category=ConvergenceWarning)

parser = argparse.ArgumentParser()

parser.add_argument("path", help="Path to the folder for which to perform the test.")
parser.add_argument("images", nargs="+" , help="Path to tif file or files.")
parser.add_argument("-s", "--sigma", type=float, default=5 , help="Sigma used to blur the ground truth. (default: 5)")
parser.add_argument("-e", "--extend", action="store_true", default=False, help="Extends the values with Spectracl indices (default: False)")
parser.add_argument("--super-extend", action="store_true", default=False, help="Extends the values with all possible Spectracl indices (default: False)")

args = parser.parse_args()
SIGMA = args.sigma
EXTEND = args.extend
SUPER_EXTEND = args.super_extend

PATH = args.path
IMAGES = args.images
lasso = joblib.load(f'{PATH}/model.pkl')
results = {}
for image in IMAGES:
    X, y = tif_to_vec(image, 0, 0, 0, SIGMA, False)

    if EXTEND:
        X = extend(X)
    
    if SUPER_EXTEND:
        X = super_extend(X)
    
    y_pred = lasso.predict(X)
    output_prediction(y_pred, image, PATH + '/test_images')
    mse_unbalanced = mean_squared_error(y, y_pred)
    mae_unbalanced = mean_absolute_error(y, y_pred)
    rmse_unbalanced = np.sqrt(mse_unbalanced)
    r2_unbalanced = r2_score(y, y_pred)
    mse_unbalanced = mean_squared_error(y, y_pred)

    results['unbalanced'] = {
        'MSE': float(mse_unbalanced),
        'MAE': float(mae_unbalanced),
        'RMSE': float(rmse_unbalanced),
        'R2': float(r2_unbalanced),
    }

    X, y = tif_to_vec(image, 0.5, 0.1, 10000, SIGMA, True)

    if EXTEND:
        X = extend(X)
    
    if SUPER_EXTEND:
        X = super_extend(X)
    y_pred = lasso.predict(X)
    mse_balanced = mean_squared_error(y, y_pred)
    mae_balanced = mean_absolute_error(y, y_pred)
    rmse_balanced = np.sqrt(mse_balanced)
    r2_balanced = r2_score(y, y_pred)
    mse_balanced = mean_squared_error(y, y_pred)
    results['balanced'] = {
        'MSE': float(mse_balanced),
        'MAE': float(mae_balanced),
        'RMSE': float(rmse_balanced),
        'R2': float(r2_balanced),
    }

with open(f'{PATH}/train.json', 'w') as f:
    json.dump(results, f, indent=4)



