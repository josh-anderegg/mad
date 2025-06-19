import random
import os
import subprocess
random.seed(42)
MAX_TRAIN_IMAGES = 2000
MAX_TEST_IMAGES = 50

TEST_PERCENTAGE = 0.1
for biome in os.listdir('data/clusters'):
    biome_str = biome.replace('.txt', '')
    print(f"Training for {biome_str}")
    with open(f'data/clusters/{biome}', 'r') as f:
        files = list(filter(lambda x: not os.path.exists(f'data/images/{x}'),f.read().split('\n')))
    file_amount = len(files)
    random.shuffle(files)
    test_count = int(TEST_PERCENTAGE * file_amount)
    test_files = files[:test_count][:MAX_TEST_IMAGES]
    model_files = files[test_count:][:MAX_TRAIN_IMAGES]
    
    result = subprocess.run(f'./lasso_train.py {' '.join(model_files)} -o "outputs/{biome_str}" -c {len(model_files)} -r {42} -p 10000' , shell=True, capture_output=True, text=True)
    print(f"Testing for {biome_str}")
    cmd = f'./lasso_predict.py {result.stdout.replace('\n', '')} {' '.join(test_files)}'
    subprocess.run(cmd, shell=True)

        
