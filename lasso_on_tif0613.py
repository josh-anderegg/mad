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

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


BANDS = ['AOT', 'B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'TCI_B', 'TCI_G', 'TCI_R']

parser = argparse.ArgumentParser()

parser.add_argument("images", nargs="+" , help="Path to tif file or files")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-l", "--lambda-count", type=int, default=25, help="Amount of Lambdas iterated over (default: 10)")
parser.add_argument("-m", "--minimal-lambda", type=int, default=-4, help="Minimal lambda used (10^-m) (default: -4)")
parser.add_argument("-g", "--generate-graphs", default=True, action="store_false", help="Set if you want the script to output graphs")
parser.add_argument("-c", "--count", type=int, default=10, help="Set the amount of images that should be used (default: 10)")
parser.add_argument("-s", "--stats", default=False, action="store_true", help="Set to perform additional stat checks (default: False)")
parser.add_argument("-o", "--output", type=str, default="outputs" , help="Path the output directory for the graphs (default: .)")
parser.add_argument("-r", "--random-seed", type=str, default=None , help="Random string used for all the randomization done.")

args = parser.parse_args()

RANDOM_SYMBOLS = string.ascii_letters + string.digits
if args.random_seed == None:
    seed = ''.join(random.choices(RANDOM_SYMBOLS, k=32))
else:
    seed = args.random_seed

if args.verbose:
    print(f'used seed: {seed}')

random.seed(seed)

image_paths = []
for pattern in args.images:
    image_paths.extend(glob.glob(pattern))

random.shuffle(image_paths)
image_paths = image_paths[:args.count]

if args.generate_graphs:
    with open(f"{args.output}/files_{timestamp}.txt", 'w') as file:
        file.write("\n".join(image_paths))

LAMBDA_COUNT = args.lambda_count
MINIMAL_LAMBDA = args.minimal_lambda

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

        pixels = normalized_data.reshape(bands, -1).T
        pixels = np.delete(pixels, [-2, -3, -4], axis=1)

        if '_mine' in src.descriptions:
            y = pixels[:, -1]
            X = np.delete(pixels, -1, axis=1)
        else:
            y = np.zeros(pixels.shape[0])
            X = pixels
        
        return X, y

lambdas = lambdas = np.logspace(MINIMAL_LAMBDA, 0, LAMBDA_COUNT).tolist()

remaining_loss = []
coefficients = []
X = []
y = []

c = 0
for path in image_paths:
    t_X, t_y = tif_to_vec(path)
    X.append(t_X)
    y.append(t_y)
    c += 1
    if c >= args.count:
        break
    if args.verbose:
        print(f"\rImage {c+1}/{args.count} loaded", end="")

if args.verbose:
    print("Loaded all images")

X = np.concatenate(X)
y = np.concatenate(y)

for i, l in enumerate(lambdas):
    if args.verbose:
        print(f"\rPerforming Lasso for Lambda {i+1}/{len(lambdas)} done", end="")
    lasso = Lasso(alpha=l)
    lasso.fit(X, y)
    coeffs = lasso.coef_
    y_pred = lasso.predict(X)
    mse = mean_squared_error(y, y_pred)
    loss = mse 

    remaining_loss.append(loss)
    coefficients.append(coeffs)

if args.verbose:
    print("All Lassos performed")

if args.generate_graphs:
    if args.verbose:
        print("Generating graphs")
    path = args.output
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
