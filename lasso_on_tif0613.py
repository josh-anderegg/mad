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

from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error
from scipy.ndimage import gaussian_filter

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


BANDS = ['AOT', 'B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'TCI_B', 'TCI_G', 'TCI_R']

parser = argparse.ArgumentParser()

parser.add_argument("images", nargs="+" , help="Path to tif file or files")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-l", "--lambda-count", type=int, default=25, help="Amount of Lambdas iterated over (default: 10)")
parser.add_argument("-m", "--minimal-lambda", type=int, default=-4, help="Minimal lambda used (10^-m) (default: -4)")
parser.add_argument("-g", "--generate-graphs", default=True, action="store_false", help="Set if you want the script to output graphs")
parser.add_argument("-c", "--count", type=int, default=10, help="Set the amount of images that should be used (default: 10)")
parser.add_argument("-o", "--output", type=str, default="outputs" , help="Path the output directory for the graphs (default: .)")
parser.add_argument("-r", "--random-seed", type=str, default=None , help="Random string used for all the randomization done.")
parser.add_argument("-p", "--pixel-count", type=int, default=1000 , help="Pixel count per image that is used to perform the lasso (default: 1000)")
parser.add_argument("--pixel-ratios", type=str, default='0.5, 0.1, 0.4' , help="Ratio between pixels taken inside, on the border and outside of the ground truth (default: 0.5, 0.1, 0.4)")
parser.add_argument("-s", "--sigma", type=float, default=5 , help="Sigma used to blur the ground truth. (default: 5)")

args = parser.parse_args()
SIGMA = args.sigma 
VERBOSE = args.verbose
LAMBDA_COUNT = args.lambda_count
MINIMAL_LAMBDA = args.minimal_lambda
RANDOM_SYMBOLS = string.ascii_letters + string.digits
IMAGES = args.images
COUNT = args.count
OUTPUT = args.output
GENERATE_GRAPHS = args.generate_graphs
PIXEL_PER_IMAGE = args.pixel_count

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

if GENERATE_GRAPHS:
    with open(f"{OUTPUT}/files_{timestamp}.txt", 'w') as file:
        file.write("\n".join(image_paths))


def tif_to_vec(path):
    with rasterio.open(path) as src:
        data = src.read()
        bands, _, _ = data.shape
        normalized_data = np.empty_like(data, dtype=np.float32)
        scaler = MinMaxScaler()
        for i in range(bands):
            band = data[i].reshape(-1, 1)
            norm_band = scaler.fit_transform(band).reshape(data.shape[1:])
            normalized_data[i] = norm_band

        # plt.imshow(normalized_data[-1], cmap='gray', vmin=0, vmax=1)
        # plt.axis('off')  
        # plt.savefig(f'outputs/pre_filtergs_{timestamp}.png')
        
        normalized_data[-1] = gaussian_filter(normalized_data[-1], sigma=SIGMA)

        # plt.imshow(normalized_data[-1], cmap='gray', vmin=0, vmax=1)
        # plt.axis('off')  
        # plt.savefig(f'outputs/post_filtergs_{timestamp}.png')

        pixels = normalized_data.reshape(bands, -1).T
        pixels = np.delete(pixels, [-2, -3, -4], axis=1) # Delete the RGB channels for visualization
        pixels = pick_quality_pixels(pixels)
        y = pixels[:, -1]
        X = np.delete(pixels, -1, axis=1)
        # if '_mine' in src.descriptions:
        #     y = pixels[:, -1]
        #     X = np.delete(pixels, -1, axis=1)
        # else:
        #     y = np.zeros(pixels.shape[0])
        #     X = pixels

        return X, y

def pick_quality_pixels(X):
    ins, edges, outs = X[(X[:, -1] == 1)], X[(X[:, -1] > 0) & (X[:, -1] < 1) ], X[(X[:, -1] == 0)]
    ins_nr = int(PIXEL_PER_IMAGE * IN)
    edges_nr = int(PIXEL_PER_IMAGE * EDGE)
    outs_nr = PIXEL_PER_IMAGE - ins_nr - edges_nr
    np.random.shuffle(ins)
    np.random.shuffle(edges)
    np.random.shuffle(outs)
    return np.concat([ins[:ins_nr], edges[:edges_nr], outs[:outs_nr]])

lambdas = lambdas = np.logspace(MINIMAL_LAMBDA, 0, LAMBDA_COUNT).tolist()

remaining_loss = []
coefficients = []
X = []
y = []

for i, path in enumerate(image_paths):
    t_X, t_y = tif_to_vec(path)
    X.append(t_X)
    y.append(t_y)
    if VERBOSE:
        print(f"\rImage {i+1}/{COUNT} loaded", end="")

if VERBOSE:
    print("Loaded all images")

X = np.concatenate(X)
y = np.concatenate(y)

for i, l in enumerate(lambdas):
    if VERBOSE:
        print(f"\rPerforming Lasso for Lambda {i+1}/{len(lambdas)} done", end="")
    lasso = Lasso(alpha=l)
    lasso.fit(X, y)
    coeffs = lasso.coef_
    y_pred = lasso.predict(X)
    mse = mean_squared_error(y, y_pred)
    loss = mse 

    remaining_loss.append(loss)
    coefficients.append(coeffs)

if VERBOSE:
    print("All Lassos performed")

if GENERATE_GRAPHS:
    if VERBOSE:
        print("Generating graphs")
    path = OUTPUT
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
    plt.savefig(f"{path}/coeffs_{timestamp}.png")

    # Plot the change in loss
    loss_lambdas = pd.DataFrame(map(lambda x: {"lambda": x[0], "loss": x[1]}, zip(lambdas, remaining_loss)))
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=loss_lambdas, x='lambda', y='loss')
    plt.xscale("log")
    plt.title("Loss for Lambda")
    plt.xlabel("Lambda")
    plt.ylabel("Loss (MSE)")
    plt.savefig(f"{path}/mse_{timestamp}.png")

    with open(f"{path}/values_{timestamp}.csv", "w") as file:
        coefficients_w = [['AOT', 'B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9']] + coefficients
        writer = csv.writer(file)
        writer.writerows(coefficients_w)
