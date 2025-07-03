import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os 
import json
for level in ['simple', 'extended', 'super_extended']:
    recs = {}
    for biome in os.listdir('outputs'):
        i = 0 
        bal, unb = 0, 0
        for test in os.listdir(f'outputs/{biome}/{level}'):
            try:
                dict = json.loads(open(f'outputs/{biome}/{level}/{test}/train.json').read())
                bal += dict['balanced']['RMSE']
                unb += dict['unbalanced']['RMSE']
                i += 1
            except:
                pass
        recs[biome] =  {'balanced':bal/i, 'unbalanced': unb/i}

    res = pd.DataFrame(recs).T
    res.to_csv(f'loss_{level}.csv')
