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
#### Code snippet

#### Possible improvements
### YOLO
#### Code snippet
#### Possible improvements
