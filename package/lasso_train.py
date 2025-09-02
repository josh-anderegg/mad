import numpy as np
import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import csv
import random
import string
import json
import os
import joblib

from datetime import datetime
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error
from concurrent.futures import ProcessPoolExecutor
from package.tif_utils import tif_to_vec, extend, super_extend

# In order to disable annoying convergence warnings, ugh
from warnings import simplefilter
from sklearn.exceptions import ConvergenceWarning
simplefilter("ignore", category=ConvergenceWarning)

SIGMA = None
VERBOSE = None
LAMBDA_COUNT = None
MINIMAL_LAMBDA = None
IMAGES = None
COUNT = None
OUTPUT = None
GENERATE_OUTPUT = None
PIXEL_PER_IMAGE = None
TRAIN_PERCENTAGE = None
EXTEND = None
SUPER_EXTEND = None
IN = None
EDGE = None
OUT = None
RANDOM_SYMBOLS = string.ascii_letters + string.digits


def get_bands():
    global EXTEND, SUPER_EXTEND, BANDS
    BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "AOT"]
    if not (EXTEND or SUPER_EXTEND):
        return BANDS
    if EXTEND:
        return ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "AOT", "NDVI", "NDRE", "GNDVI", "NDMI", "MSI", "NDWI", "MNDWI", "NBR", "NBR2", "NDBI", "NDSI", "NDVI705", "NDTI", "AMWI"]

    if SUPER_EXTEND:
        new_bands = BANDS.copy()
        for bandi in BANDS:
            for bandj in BANDS:
                if bandi != bandj:
                    new_bands.append(f'{bandi}-{bandj}')
        return new_bands


def parse_args(args):
    global SIGMA, VERBOSE, LAMBDA_COUNT, MINIMAL_LAMBDA, RANDOM_SYMBOLS, IMAGES, COUNT, OUTPUT, GENERATE_OUTPUT, PIXEL_PER_IMAGE, TRAIN_PERCENTAGE, EXTEND, SUPER_EXTEND, IN, EDGE, OUT, BANDS, SEED
    SIGMA = args.sigma
    VERBOSE = args.verbose
    LAMBDA_COUNT = args.lambda_count
    MINIMAL_LAMBDA = args.minimal_lambda
    IMAGES = args.images
    COUNT = args.count
    OUTPUT = args.output
    GENERATE_OUTPUT = args.generate_output
    PIXEL_PER_IMAGE = args.pixel_count
    TRAIN_PERCENTAGE = args.train_percentage
    EXTEND = args.extend
    SUPER_EXTEND = args.super_extend
    BANDS = get_bands()

    try:
        IN, EDGE, OUT = map(float, args.pixel_ratios.split(','))
        if not abs(IN + EDGE + OUT - 1.0) < 1e-6:
            raise ValueError("Split ratios must sum to 1.0")
    except Exception:
        raise ValueError(f"Could not parse in split values: {args.pixel_ratios}, should be of the form IN, EDGE, OUT. All of them being floats.")

    if args.random_seed is None:
        SEED = ''.join(random.choices(RANDOM_SYMBOLS, k=32))
    else:
        SEED = args.random_seed

    if VERBOSE:
        print(f'used seed: {SEED}')


def load_set(image_paths, tstr="", sample_pixels=True, silent=False):
    global IN, EDGE, PIXEL_PER_IMAGE, SIGMA, EXTEND, SUPER_EXTEND, VERBOSE
    X = []
    y = []

    size = 0
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(tif_to_vec, path, IN, EDGE, PIXEL_PER_IMAGE, SIGMA, BANDS + ["Mine"], sample_pixels): path for path in image_paths}
        for i, future in enumerate(futures):
            try:
                t_X, t_y = future.result()
                if EXTEND:
                    t_X = extend(t_X)
                if SUPER_EXTEND:
                    t_X = super_extend(t_X)
                X.append(t_X)
                y.append(t_y)
                if VERBOSE and not silent:
                    size += t_X.nbytes + t_y.nbytes  # type: ignore
                    if (size / (1024**3)) > 10:
                        break
                    print(f"\rloaded {i + 1}/{len(image_paths)} {tstr} images, {size / (1024**3):2f} GB used", end="")
            except Exception as e:
                if VERBOSE and not silent:
                    print(f"Concurrency error happened, skipped an image \n{e}")

    if VERBOSE and not silent:
        print(f"\nLoaded all {tstr} images")

    X = np.concatenate(X)
    y = np.concatenate(y)
    return X, y


def train(X_train, y_train, X_validation, y_validation):
    global MINIMAL_LAMBDA, LAMBDA_COUNT, VERBOSE

    coefficients = []
    remaining_loss = []
    lambdas = lambdas = np.logspace(MINIMAL_LAMBDA, 0, LAMBDA_COUNT).tolist()
    best_model = Lasso()
    best_loss = 1 << 128

    for i, l in enumerate(lambdas):
        if VERBOSE:
            print(f"\rPerforming Lasso for Lambda {i + 1}/{len(lambdas)} done", end="")
        lasso = Lasso(alpha=l)
        lasso.fit(X_train, y_train)
        coeffs = lasso.coef_
        y_pred = lasso.predict(X_validation)
        mse = mean_squared_error(y_validation, y_pred)
        loss = mse
        remaining_loss.append(loss)
        coefficients.append(coeffs)
        if loss < best_loss:
            best_model = lasso
            best_loss = loss

    if VERBOSE:
        print("\nAll Lassos performed")

    return lambdas, coefficients, best_model, remaining_loss


def generate_output(lambdas, coefficients, best_model, remaining_loss, train_images, validation_images):
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
        coefficients_w = [BANDS] + coefficients
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
        'validation_files': validation_images,
        'parameters': {
            'sigma': SIGMA,
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
    joblib.dump(best_model, f'{path}/model.pkl')


def run(args):
    global SEED
    parse_args(args)
    random.seed(SEED)

    image_paths = []
    for pattern in IMAGES:
        image_paths.extend(glob.glob(pattern))

    random.shuffle(image_paths)
    image_paths = image_paths[:COUNT]

    train_count = int(COUNT * TRAIN_PERCENTAGE)
    validation_count = COUNT - train_count

    train_images = image_paths[:train_count]
    validation_images = image_paths[train_count:][:validation_count]

    X_train, y_train = load_set(train_images, tstr="train", sample_pixels=True)
    X_validation, y_validation = load_set(validation_images, tstr="test", sample_pixels=False)

    lambdas, coefficients, best_model, remaining_loss = train(X_train, y_train, X_validation, y_validation)

    generate_output(lambdas, coefficients, best_model, remaining_loss, train_images, validation_images)
