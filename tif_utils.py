import rasterio
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler
from scipy.ndimage import gaussian_filter

def tif_to_vec(path, IN, EDGE, PIXEL_PER_IMAGE, SIGMA, sample_pixels=True):
    with rasterio.open(path) as src:
        data = src.read()
        bands, _, _ = data.shape
        normalized_data = np.empty_like(data, dtype=np.float32)
        scaler = MinMaxScaler()
        for i in range(bands):
            band = data[i].reshape(-1, 1)
            norm_band = scaler.fit_transform(band).reshape(data.shape[1:])
            normalized_data[i] = norm_band

        normalized_data[-1] = gaussian_filter(normalized_data[-1], sigma=SIGMA)
        pixels = normalized_data.reshape(bands, -1).T
        # pixels = np.delete(pixels, [-2, -3, -4], axis=1) # Delete the RGB channels for visualization
        if sample_pixels:
            pixels = pick_quality_pixels(pixels, IN, EDGE, PIXEL_PER_IMAGE)
        y = pixels[:, -1]
        X = np.delete(pixels, -1, axis=1)
        return X, y

def pick_quality_pixels(X, IN, EDGE, PIXEL_PER_IMAGE):
    ins, edges, outs = X[(X[:, -1] == 1)], X[(X[:, -1] > 0) & (X[:, -1] < 1) ], X[(X[:, -1] == 0)]
    ins_nr = int(PIXEL_PER_IMAGE * IN)
    edges_nr = int(PIXEL_PER_IMAGE * EDGE)
    outs_nr = PIXEL_PER_IMAGE - ins_nr - edges_nr
    np.random.shuffle(ins)
    np.random.shuffle(edges)
    np.random.shuffle(outs)
    return np.concatenate([ins[:ins_nr], edges[:edges_nr], outs[:outs_nr]])

def output_prediction(prediction_band, image_path, output_path):
    os.makedirs(output_path, exist_ok=True)
    with rasterio.open(image_path) as src:
        existing_data = src.read()
        meta = src.meta.copy()
        height = src.height
        width = src.width
        prediction_band = prediction_band.reshape((height, width))
        original_band_names = [src.descriptions[i] if src.descriptions[i] else f"Band {i}" for i in range(existing_data.shape[0])]
    path = image_path.split('/')[-1]
    
    # Kinda sketchy to do the type conversion here, should be fine though for showcase purposes
    meta.update(count=existing_data.shape[0] + 1, dtype='float32')

    with rasterio.open(f"{output_path}/prediction_{path}", "w", **meta) as dst:
        for i in range(existing_data.shape[0]):
            dst.write(existing_data[i], i + 1)
            dst.set_band_description(i+1, original_band_names[i])
        dst.write(prediction_band, existing_data.shape[0] + 1)
        dst.set_band_description(existing_data.shape[0] + 1, "Prediction")

def safe_index_calc(numerator, denominator):
    with np.errstate(divide='ignore', invalid='ignore'):
        index = (numerator - denominator) / (numerator + denominator)
    if np.isnan(index).any():
        index = np.zeros_like(index)
    return index
(B4, B3, B2, B5, B6, B7, B8, B8A, B9, B11, B12, AOT) = range(0, 12)

def extend(X):
    NDVI = safe_index_calc(X[:, B8], X[:, B4])
    NDRE = safe_index_calc(X[:, B8A], X[:, B5])
    GNDVI = safe_index_calc(X[:, B8], X[:, B3])
    NDMI = safe_index_calc(X[:, B8], X[:, B11])
    MSI = safe_index_calc(X[:, B11], X[:, B8])
    NDWI = safe_index_calc(X[:, B3], X[:, B8])
    MNDWI = safe_index_calc(X[:, B3], X[:, B11])
    NBR = safe_index_calc(X[:, B8], X[:, B12])
    NBR2 = safe_index_calc(X[:, B11], X[:, B12])
    NDBI = safe_index_calc(X[:, B11], X[:, B8])
    NDSI = safe_index_calc(X[:, B3], X[:, B11])
    NDVI705 = safe_index_calc(X[:, B5], X[:, B4])
    NDTI = safe_index_calc(X[:, B4], X[:, B3])
    AMWI = safe_index_calc(X[:, B4], X[:, B2])
    return np.column_stack((X, NDVI, NDRE, GNDVI, NDMI, MSI, NDWI, MNDWI, NBR, NBR2, NDBI, NDSI, NDVI705, NDTI, AMWI))