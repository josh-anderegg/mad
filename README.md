# Directory structure:

```.
├── data (Anything input related)
│   ├── clusters (Has files needed for determining which image is in which eco regions)
│   ├── Ecoregions2017 (Data for fetching ecorregion)
│   ├── grids (Contains the grids for pulling the satellite images)
│   ├── images (.tif images for lasso and yolo)
│   ├── maus (maus dataset)
│   ├── temp (temp for creating data)
│   └── dataset (Datasets for yolo training, follows yolo typical formatting)
├── journal (slides and related notes)
├── outputs (outputs from both lasso and yolo)
├── package (programs realted to final product)
└── scripts (helper scripts for organising files or additional downloading)
```

# Installation

In order to install the package via pip simply run `pip install .` and a binary called `mad` should be added to your path.
## Package functionality

```
mad
├── setup
├── grid
│   ├── create (Create an equidistant grid for the globe)
│   └── download (Provide a grid to be downloaded using GEE)
├── lasso
│   ├── train (temp for creating data)
│   └── predict (To use lasso to predict mine coverage in some images)
└── yolo
    ├── create (For creating a dataset based on polygons and .tif images)
    ├── train (For training a yolo model according to the yolo dataset)
    └── predict (To do a quick prediction for an image)

```

For each command run `mad [command] --help` in order to get a more precise description for the corresponding parameters.

# TODO
 - [ ] Run YOLO for the baseline dataset. 
 - [ ] Clean baseline dataset from snowy/otherwise bad images. 
 - [ ] Create dataset using perturbed cleaned images. 
 - [ ] ... 

