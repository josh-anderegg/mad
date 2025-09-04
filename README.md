# MAD
`mad` is a command line interface tool, allowing for the detection of mining activities worldwide. It consists of a pipeline for the downloading of satellite images, creation of datasets using the satellite images and ultimately training and predicing based on the created datasets.

# Installation
In order to install the package via pip simply run `pip install .` and a binary called `mad` should be added to your path.

Additionally some bash scripts have further dependencies that have to be installed beforehand:
- `jq` for interpreting the quality metadata files.
- `gdal` for interacting with any satellite images.
- `gdal-python-tools` for some additional gdal functionality
All other used bash commands should be standard on most systems.

## Modules
MAD is designed to be as modular as possible. In general there are 4 major modules.
1. Setup (`mad setup ...`)
2. Database creation (`mad database ...`)
3. Lasso training (`mad lasso ...`)
4. YOLO training (`mad yolo ...`)

### Setup
The setup takes care of downloading the necessary data to train models. Minimally we need: 
1. the MAUS dataset, which contains polygons surrounding excavation sites. (~ MB)
2. the ecoregions dataset, which contains polygons highlighting different ecoregions, though as biomes for training. (~ MB)
3. the global country dataset, which contains polygons of all countries (~MB)
4. the sentinel 2 satellite imagery, which can become arbitrarily large. (~ TB)

### Database
The databse module allows for the creation, expansion and definition of datasets. Subcommands include:
1. `create` For creating the necessary folder structure, gathering which global tiles are part of the database and how they are separated into train, test and validation sets. (~seconds)
2. `index` For downloading all of the necessary quality metadata, used to download the images later. (~hours)
3. `download` Downloads all the images, for which the quality metadata is available. Allows for different modes in which these images are created.

#### Code snippet
```bash
mad database create "all-australia" "Australia" # Defines all of Australia as the tile source
mad database index "all-australia" # Downloads the index for all the images inside of the database
mad database download "all-australia" --bands TCI B9 B8 B7 --composition first # Downloads all of the images with the selected bands and simply takes the first/best quality image.
```

#### Possible improvements
- [ ] Add `resolve` to resolve blame conflicts where image quality was low to try another download technique
- [ ] Allow for smarter caching/combining of bands/images such that not everything is redownloaded for the same image.
- [ ] Allow to define the amount of bytes used for a single pixel: Would allow smaller database at the cost of fidelity and needs definition of the range of values.

### Lasso
The lasso module allows to train a Lasso regressor on a database. Subcommands include:
1. `train` Train a regressor based on a folder containing satellite images.
2. `predict` Using a trained regressor, perform a prediction run with performance metrics and graphs generated.

#### Code snippet
```bash
mad lasso train "data/all-australia" "outputs/all-australia"
mad lasso predict "data/all-australia" "outputs/all-australia"
```

#### Possible improvements
- [ ] Ensure 100% compatibility with all the YOLO operations, namely:
    - Seperate the outputs into different output sub-folders.
    - Guarantee that all satellite image storage formats are supported. (`tif`, `.jp2`)
- [ ] Allow for geolocation of prediction to enable the combination of geolocated YOLO outputs and Lasso outputs.
### YOLO
The YOLO module allows to generate YOLO compatible datasets based on the downloaded database, as well as the training based on such a dataset and the prediction of a a trained YOLO model. Subcommands include:
1. `create` Creates a dataset basedo on a database and a polygon collection.
2. `train` Train a model based on a created dataset.
3. `predict` Perform the prediction for a created dataset and make the output georeferenced.
#### Code snippet
```bash
mad yolo create "data/all-australia" "data/all-australia-dataset" --polygons"data/geometries/maus.gpkg"
mad yolo train "data/all-australia-dataset"
mad yolo predict "data/all-australia-dataset" "outputs/all-australia-dataset/train/predict/models/best.pt"
```
#### Possible improvements
- [ ] Avoid data inflation by caching/tracking created images per image instead of per tile.
- [ ] Integrate nicely with the hyperparametrization that YOLO allows.

# Project layout
```
.
├── data
├── journal
├── legacy
├── outputs
├── package
├── scripts
```

Generally everything concerning the `mad` executable is inside of `package`, where additional scripts that are not integrated with the executable can be found in `scripts`. `legacy` contains any scripts, that should not be run/can't be run without further effort, an example would be a previous version to download GEE images, which is still there in case someone would like to use GEE together with a Python package.

`data` contains all the accessible data from within the mad package, sometimes outputs are also stored inside of `data` in case the output is used down the road (e.g. datasets derrived from the databse). `outputs` contains everything that can be considered a final output from the executable, like the `.gkpg` containing the classified mine locations from the model.

`journal` contains all the presentations created within the scope of the project. Finally `pyproject.toml` contains everything needed for `pip` to install all dependencies.
