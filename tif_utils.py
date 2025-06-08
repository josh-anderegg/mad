import rasterio
import numpy as np

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
        pixels = np.delete(pixels, [-2, -3, -4], axis=1) # Delete the RGB channels for visualization
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

    with rasterio.open(image_path) as src:
        existing_data = src.read()
        meta = src.meta.copy()
        height = src.height
        width = src.width
        prediction_band = prediction_band.reshape((height, width))
        original_band_names = [src.descriptions[i] if src.descriptions[i] else f"Band {i}" for i in range(existing_data.shape[0])]
    path = image_path.split('/')[-1]

    meta.update(count=existing_data.shape[0] + 1)

    with rasterio.open(f"{output_path}/prediction_{path}", "w", **meta) as dst:
        for i in range(existing_data.shape[0]):
            dst.write(existing_data[i], i + 1)
            dst.set_band_description(i+1, original_band_names[i])
        dst.write(prediction_band, existing_data.shape[0] + 1)
        dst.set_band_description(existing_data.shape[0] + 1, "Prediction")

