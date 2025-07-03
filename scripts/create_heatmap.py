import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os 
import json
super = ['B4', 'B3', 'B2', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12', 'AOT', 'B4-B3', 'B4-B2', 'B4-B5', 'B4-B6', 'B4-B7', 'B4-B8', 'B4-B8A', 'B4-B9', 'B4-B11', 'B4-B12', 'B4-AOT', 'B3-B4', 'B3-B2', 'B3-B5', 'B3-B6', 'B3-B7', 'B3-B8', 'B3-B8A', 'B3-B9', 'B3-B11', 'B3-B12', 'B3-AOT', 'B2-B4', 'B2-B3', 'B2-B5', 'B2-B6', 'B2-B7', 'B2-B8', 'B2-B8A', 'B2-B9', 'B2-B11', 'B2-B12', 'B2-AOT', 'B5-B4', 'B5-B3', 'B5-B2', 'B5-B6', 'B5-B7', 'B5-B8', 'B5-B8A', 'B5-B9', 'B5-B11', 'B5-B12', 'B5-AOT', 'B6-B4', 'B6-B3', 'B6-B2', 'B6-B5', 'B6-B7', 'B6-B8', 'B6-B8A', 'B6-B9', 'B6-B11', 'B6-B12', 'B6-AOT', 'B7-B4', 'B7-B3', 'B7-B2', 'B7-B5', 'B7-B6', 'B7-B8', 'B7-B8A', 'B7-B9', 'B7-B11', 'B7-B12', 'B7-AOT', 'B8-B4', 'B8-B3', 'B8-B2', 'B8-B5', 'B8-B6', 'B8-B7', 'B8-B8A', 'B8-B9', 'B8-B11', 'B8-B12', 'B8-AOT', 'B8A-B4', 'B8A-B3', 'B8A-B2', 'B8A-B5', 'B8A-B6', 'B8A-B7', 'B8A-B8', 'B8A-B9', 'B8A-B11', 'B8A-B12', 'B8A-AOT', 'B9-B4', 'B9-B3', 'B9-B2', 'B9-B5', 'B9-B6', 'B9-B7', 'B9-B8', 'B9-B8A', 'B9-B11', 'B9-B12', 'B9-AOT', 'B11-B4', 'B11-B3', 'B11-B2', 'B11-B5', 'B11-B6', 'B11-B7', 'B11-B8', 'B11-B8A', 'B11-B9', 'B11-B12', 'B11-AOT', 'B12-B4', 'B12-B3', 'B12-B2', 'B12-B5', 'B12-B6', 'B12-B7', 'B12-B8', 'B12-B8A', 'B12-B9', 'B12-B11', 'B12-AOT', 'AOT-B4', 'AOT-B3', 'AOT-B2', 'AOT-B5', 'AOT-B6', 'AOT-B7', 'AOT-B8', 'AOT-B8A', 'AOT-B9', 'AOT-B11', 'AOT-B12']
for level in ['simple', 'extended', 'super_extended']:
    biomes = []
    for biome in os.listdir('outputs'):
        entry = {}
        match level:
            case 'simple':
                entry = {'Name': biome, 'B3': 0, 'B4': 0, 'B2': 0, 'B5': 0, 'B6': 0, 'B7': 0, 'B8': 0, 'B8A': 0, 'B9': 0, 'B11': 0, 'B12': 0, 'AOT': 0}
            case 'extended':
                entry = {'Name': biome, 'B3': 0, 'B4': 0, 'B2': 0, 'B5': 0, 'B6': 0, 'B7': 0, 'B8': 0, 'B8A': 0, 'B9': 0, 'B11': 0, 'B12': 0, 'AOT': 0, 'NDVI': 0, 'NDRE': 0, 'GNDVI': 0, 'NDMI': 0, 'MSI': 0, 'NDWI': 0, 'MNDWI': 0, 'NBR': 0, 'NBR2': 0, 'NDBI': 0, 'NDSI': 0, 'NDVI1705': 0, 'NDTI': 0, 'AMWI': 0}
            case 'super_extended':
                entry = {e: 0 for e in super}
                entry['Name'] = biome

        coeffs = [json.loads(open(f'outputs/{biome}/{level}/{test}/meta.json').read())['best_ceofficients'] for test in os.listdir(f'outputs/{biome}/{level}')]
        for j in coeffs:
            for e in j:
                for k in e:
                    try:
                        entry[k] += 1
                    except:
                        pass
        biomes.append(entry)
    sns.set_theme()

    df = pd.DataFrame(biomes)
    df.set_index('Name', inplace=True)
    df_normalized = df.div(df.max(axis=1), axis=0).fillna(0)
    rows, cols = df_normalized.shape
    f_width = max(12, cols * 1)
    f_height = max(12, rows * 1)

    f, ax = plt.subplots(figsize=(f_width, f_height))
    sns.heatmap(df_normalized, fmt="d", ax=ax)
    plt.tight_layout()
    plt.savefig(f'heatmap_{level}.png', dpi=512)