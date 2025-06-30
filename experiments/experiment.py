import random
import os
import subprocess
MAX_TRAIN_IMAGES = 100
MAX_TEST_IMAGES = 10
TEST_PERCENTAGE = 0.01
PIXEL_COUNT = 5000

# Requires the data to be clustered
for biome in os.listdir('data/clusters'):
    biome_str = biome.replace('.txt', '')

    with open(f'data/clusters/{biome}', 'r') as f:
        files = list(filter(lambda x: not os.path.exists(f'data/images/{x}'),f.read().split('\n')))

    file_amount = len(files)
    random.shuffle(files)
    
    test_count = int(TEST_PERCENTAGE * file_amount)
    test_files = files[:test_count][:MAX_TEST_IMAGES]
    model_files = files[test_count:][:MAX_TRAIN_IMAGES]

    train_cmd_ext = f'./lasso_train.py {' '.join(model_files)} -o "outputs/{biome_str}_extended" -c {len(model_files)} -p {PIXEL_COUNT} -e -v'
    subprocess.run(train_cmd_ext , shell=True)
    test_cmd_ext = f'./lasso_predict.py outputs/{biome_str}_extended/latest {' '.join(test_files)} -e'
    subprocess.run(test_cmd_ext, shell=True)

    train_cmd_ext = f'./lasso_train.py {' '.join(model_files)} -o "outputs/{biome_str}_super_extended" -c {len(model_files)} -p {PIXEL_COUNT} --super-extend -v'
    subprocess.run(train_cmd_ext , shell=True)
    test_cmd_ext = f'./lasso_predict.py outputs/{biome_str}_extended/latest {' '.join(test_files)} --super-extend'
    subprocess.run(test_cmd_ext, shell=True)

    train_cmd_smp = f'./lasso_train.py {' '.join(model_files)} -o "outputs/{biome_str}_simple" -c {len(model_files)} -p {PIXEL_COUNT} -v'
    subprocess.run(train_cmd_smp , shell=True)
    test_cmd_smp = f'./lasso_predict.py outputs/{biome_str}_simple/latest {' '.join(test_files)}'
    subprocess.run(test_cmd_smp, shell=True)

        
