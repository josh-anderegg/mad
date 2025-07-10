from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os 
import json
BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = BASE_DIR / 'outputs/lasso/results'

for level in ['simple', 'extended', 'super_extended']:
    recs = {}
    for biome in os.listdir(RESULT_DIR):
        i = 0 
        bal, unb = 0, 0
        for test in os.listdir(RESULT_DIR / f'{biome}/{level}'):
            try:
                dict = json.loads(open(RESULT_DIR / f'{biome}/{level}/{test}/train.json').read())
                bal += dict['balanced']['RMSE']
                unb += dict['unbalanced']['RMSE']
                i += 1
            except:
                pass
        recs[biome] =  {'balanced':bal/i, 'unbalanced': unb/i}

    res = pd.DataFrame(recs).T
    res.to_csv(f'outputs/lasso/meta/loss_{level}.csv')
