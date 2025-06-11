#!/usr/bin/env python3

import rasterio
import numpy as np
import argparse
import glob 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import csv 
import random
import string
import json 
import os

from datetime import datetime
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error
from concurrent.futures import ProcessPoolExecutor
from tif_utils import tif_to_vec, output_prediction

# In order to disable annoying convergence warnings, ugh
from warnings import simplefilter
from sklearn.exceptions import ConvergenceWarning
simplefilter("ignore", category=ConvergenceWarning)


BANDS = ['AOT', 'B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'TCI_B', 'TCI_G', 'TCI_R']

parser = argparse.ArgumentParser()

parser.add_argument("images", nargs="+" , help="Path to tif file or files")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-l", "--lambda-count", type=int, default=25, help="Amount of Lambdas iterated over (default: 10)")
parser.add_argument("-m", "--minimal-lambda", type=int, default=-4, help="Minimal lambda used (10^-m) (default: -4)")
parser.add_argument("-g", "--generate-output", default=True, action="store_false", help="Set if you want the script to create output")
parser.add_argument("-c", "--count", type=int, default=10, help="Set the amount of images that should be used (default: 10)")
parser.add_argument("-o", "--output", type=str, default="outputs" , help="Path the output directory for the graphs (default: .)")
parser.add_argument("-r", "--random-seed", type=str, default=None , help="Random string used for all the randomization done.")
parser.add_argument("-p", "--pixel-count", type=int, default=1000 , help="Maximal pixel count per image that is used to perform the lasso (default: 1000)")
parser.add_argument("-e", "--example-count", type=int, default=0, help="Number of output example images to showcase the prediction accuaracy. (default: 0)")
parser.add_argument("--pixel-ratios", type=str, default='0.5, 0.1, 0.4' , help="Ratio between pixels taken inside, on the border and outside of the ground truth (default: 0.5, 0.1, 0.4)")
parser.add_argument("-s", "--sigma", type=float, default=5 , help="Sigma used to blur the ground truth. (default: 5)")
parser.add_argument("--train-percentage", type=float, default=0.8, help="Percentage of the images that are used for the training vs. testing (default: 0.8)")

args = parser.parse_args()
SIGMA = args.sigma 
VERBOSE = args.verbose
LAMBDA_COUNT = args.lambda_count
MINIMAL_LAMBDA = args.minimal_lambda
RANDOM_SYMBOLS = string.ascii_letters + string.digits
IMAGES = args.images
COUNT = args.count
OUTPUT = args.output
GENERATE_OUTPUT = args.generate_output
PIXEL_PER_IMAGE = args.pixel_count
TRAIN_PERCENTAGE = args.train_percentage
EXAMPLE_COUNT = args.example_count

try:
    IN, EDGE, OUT = map(float, args.pixel_ratios.split(','))
    if not abs(IN + EDGE + OUT - 1.0) < 1e-6:
        raise ValueError("Split ratios must sum to 1.0")
except:
    raise ValueError(f"Could not parse in split values: {args.pixel_ratios}, should be of the form IN, EDGE, OUT. All of them being floats.")


if args.random_seed == None:
    SEED = ''.join(random.choices(RANDOM_SYMBOLS, k=32))
else:
    SEED = args.random_seed

if VERBOSE:
    print(f'used seed: {SEED}')

random.seed(SEED)

image_paths = []
for pattern in IMAGES:
    image_paths.extend(glob.glob(pattern))

random.shuffle(image_paths)
image_paths = image_paths[:COUNT]

train_count = int(COUNT * TRAIN_PERCENTAGE)
test_count = COUNT - train_count

train_images = image_paths[:train_count]
test_images = image_paths[train_count:][:test_count]
def load_set(image_paths, tstr = "", sample_pixels = True, silent = False):
    X = []
    y = []

    size = 0
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(tif_to_vec, path, IN, EDGE, PIXEL_PER_IMAGE, SIGMA, sample_pixels): path for path in image_paths}
        for i, future in enumerate(futures):
            try: 
                t_X, t_y = future.result()
                X.append(t_X)
                y.append(t_y)
                if VERBOSE and not silent:
                    size += t_X.nbytes + t_y.nbytes
                    print(f"\rloaded {i+1}/{len(image_paths)} {tstr} images, {size / (1024**3):2f} GB used", end="")
            except Exception as e:
                if VERBOSE and not silent:
                    print(f"Concurrency error happened, skipped an image \n{e}")

    if VERBOSE and not silent:
        print(f"\nLoaded all {tstr} images")

    X = np.concatenate(X)
    y = np.concatenate(y)
    return X, y

X_train, y_train = load_set(train_images, tstr="train", sample_pixels=True)
X_test, y_test = load_set(test_images, tstr="test", sample_pixels=False)

coefficients = []
remaining_loss = []
lambdas = lambdas = np.logspace(MINIMAL_LAMBDA, 0, LAMBDA_COUNT).tolist()
best_model = Lasso()
best_loss = 1 << 128

for i, l in enumerate(lambdas):
    if VERBOSE:
        print(f"\rPerforming Lasso for Lambda {i+1}/{len(lambdas)} done", end="")
    lasso = Lasso(alpha=l)
    lasso.fit(X_train, y_train)
    coeffs = lasso.coef_
    y_pred = lasso.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    loss = mse 
    remaining_loss.append(loss)
    coefficients.append(coeffs)
    if loss < best_loss:
        best_model = lasso
        best_loss = loss

if VERBOSE:
    print("\nAll Lassos performed")

if GENERATE_OUTPUT:
    if VERBOSE:
        print("Generating ouptut")
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = f'{OUTPUT}/{timestamp}'
    os.makedirs(path)

    
    combined = zip(lambdas, coefficients)
    table = []

    for (l, coeffs) in combined:
        result = {}
        result['lambda'] = l
        for i, coeff in enumerate(coeffs):
            if i >= 12:
                continue
            result[BANDS[i]] = coeff
        table.append(result)

    df_result = pd.DataFrame(table)
    df_long = df_result.melt(id_vars='lambda', var_name='coefficient', value_name='magnitude')

    # Plot the change in coefficients
    plt.figure(figsize=(10, 6))
    sns.relplot(data=df_long, kind='line', x='lambda', y='magnitude', hue='coefficient', palette="Paired")
    plt.xscale("log") 
    plt.title("Lasso Coefficients for a Lambda")
    plt.xlabel("Lambda")
    plt.ylabel("Coefficient Value")
    plt.savefig(f"{path}/coeffs.png")

    # Plot the change in loss
    loss_lambdas = pd.DataFrame(map(lambda x: {"lambda": x[0], "loss": x[1]}, zip(lambdas, remaining_loss)))
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=loss_lambdas, x='lambda', y='loss')
    plt.xscale("log")
    plt.title("Loss for Lambda")
    plt.xlabel("Lambda")
    plt.ylabel("Loss (MSE)")
    plt.savefig(f"{path}/mse.png")

    with open(f"{path}/values.csv", "w") as file:
        coefficients_w = [['AOT', 'B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9']] + coefficients
        writer = csv.writer(file)
        writer.writerows(coefficients_w)

    coefficients.reverse()
    best_coeffcients = []
    for iteration in coefficients:
        if len(list(filter(lambda x: abs(x) > 0, iteration))) >= 3:
            best_coeffcients = sorted(list(filter(lambda x: abs(x[1]) > 0, zip(BANDS, iteration))), key=lambda x: abs(x[1]), reverse=True)
            best_coeffcients = list(map(lambda x: {x[0]: float(x[1])}, best_coeffcients))
            break

    meta_collection = {
        'seed': SEED, 
        'best_ceofficients': best_coeffcients, 
        'train_files': train_images, 
        'test_files': test_images, 
        'parameters': {
            'sigma' : SIGMA,
            'lambda_count': LAMBDA_COUNT,
            'minimal_lambda': MINIMAL_LAMBDA,
            'lambdas': lambdas,
            'count': COUNT,
            'pixel_count': PIXEL_PER_IMAGE,
            'in': IN,
            'edge': EDGE,
            'out': OUT
        }
    }

    with open(f'{path}/meta.json', 'w') as file:
        json.dump(meta_collection, file, indent=4)
    
    symlink_path = f'{OUTPUT}/latest'
    if os.path.exists(symlink_path) or os.path.islink(symlink_path):
        os.remove(symlink_path)
    
    target_abs = os.path.abspath(path)
    symlink_abs = os.path.abspath(symlink_path)
    os.symlink(target_abs, symlink_abs, target_is_directory=True)

    for i in range(EXAMPLE_COUNT):
        if VERBOSE:
            print(f"\rGenerating example output {i+1}/{EXAMPLE_COUNT}", end="")

        X_exemplify, _ = load_set([test_images[i]], "example", False, silent=True)
        y_example = best_model.predict(X_exemplify)
        output_prediction(y_example, test_images[i], OUTPUT + '/' + timestamp)
    print("\nAll examples output")


