from pathlib import Path
import random
import os
import subprocess

MAX_TRAIN_IMAGES = 600
MAX_TEST_IMAGES = 10
TEST_PERCENTAGE = 0.01
PIXEL_COUNT = 5000
BASE_DIR = Path(__file__).resolve().parent.parent

# Execute the simple, extended and super extened lasso for each biome once

for biome in os.listdir(BASE_DIR / "data/clusters"):
    biome_str = biome.replace(".txt", "")

    with open(BASE_DIR / f"data/clusters/{biome}", "r") as f:
        files = list(
            filter(
                lambda x: not os.path.exists(BASE_DIR / f"data/images/{x}"),
                f.read().split("\n"),
            )
        )

    file_amount = len(files)
    random.shuffle(files)

    test_count = int(TEST_PERCENTAGE * file_amount)
    test_files = files[:test_count][:MAX_TEST_IMAGES]
    model_files = files[test_count:][:MAX_TRAIN_IMAGES]
    result_dir = str(BASE_DIR / f"outputs/lasso/results/{biome_str}")

    print("Extended run")
    train_cmd_ext = (
        BASE_DIR
        / f'./lasso_train.py {" ".join(model_files)} -o "{result_dir}/extended" -c {len(model_files)} -p {PIXEL_COUNT} -e -v'
    )
    subprocess.run(train_cmd_ext, shell=True)
    test_cmd_ext = (
        BASE_DIR
        / f'./lasso_predict.py {result_dir}/extended/latest {" ".join(test_files)} -e'
    )
    subprocess.run(test_cmd_ext, shell=True)

    print("Super extended run")
    train_cmd_supext = (
        BASE_DIR
        / f'./lasso_train.py {" ".join(model_files)} -o "{result_dir}/super_extended" -c {len(model_files)} -p {PIXEL_COUNT} --super-extend -v'
    )
    subprocess.run(train_cmd_supext, shell=True)
    test_cmd_supext = (
        BASE_DIR
        / f'./lasso_predict.py {result_dir}/super_extended/latest {" ".join(test_files)} --super-extend'
    )
    subprocess.run(test_cmd_supext, shell=True)

    print("Simple run")
    train_cmd_smp = (
        BASE_DIR
        / f'./lasso_train.py {" ".join(model_files)} -o "{result_dir}/simple" -c {len(model_files)} -p {PIXEL_COUNT} -v'
    )
    subprocess.run(train_cmd_smp, shell=True)
    test_cmd_smp = (
        BASE_DIR
        / f'./lasso_predict.py {result_dir}/simple/latest {" ".join(test_files)}'
    )
    subprocess.run(test_cmd_smp, shell=True)
