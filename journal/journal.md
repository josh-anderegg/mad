# MAD journal

## Technical description 
The general idea behind MAD is to allow to detect mining excavation sites using machine learning techniques. Currently there's a pipeline in place to train a Lasso regressor and yolo models respectively. 

Models are trained by generating datasets from an initial satellite image dataset that consists of raw `.tif` images consisting of 13 bands respectively and being taken by the sentinel L2A satellite.

### Modules
MAD is designed to be as modular as possible. In general there are 4 major modules.
1. Setup (`mad setup ...`)
2. Dataset creation (`mad dataset ...`)
3. Lasso training (`mad lasso ...`)
4. YOLO training (`mad yolo ...`)

#### Setup
The setup takes care of downloading the necessary data to train models. Minimally we need: 
1. the MAUS dataset, which contains polygons surrounding excavation sites. (~ MB)
2. the ecoregions dataset, which contains polygons highlighting different ecoregions, though as biomes for training. (~ MB)
3. the sentinel 2 satellite imagery. (~ TB)
Depending on the flags you give the cli, more or less data will be downloaded.

More on the imagery in [imagery](#imagery).

#### Dataset creation
Both lasso and yolo consume a dataset of images in order to perform their respective training and evaluation steps. Thus the primary difference between then different models we train is not only the hyperparameters provided but the underlying dataset used. In order to control this you're required to generate a dataset for a given training run, depending on the parameters used the datasets will differ in some regards.

The creation follows a sponge function like structure. The initial data (large `.tif` images) is separated into train, validation and testing sets (absorption). 

Each of the sets is then squeezed i.e. filtered. Some satellite images might have nodata columns at the edge of the swath. Or it might have cloud coverage in important spots. In these cases no the whole image is scrapped, but only the undesirable spots are unused.

Each set is then expanded. In the baseline case this only means that the satellite image is rasterized into 640px x 640px images to then be fed to the machine learning paradigm used. More advanced expansion might be randomized rasterization with rotation, translation and zooming out, or changing the amount of true negatives in the final dataset.

In a final step, the resulting images from the expansion are labelled in case of yolo training.
```

                   ┌─────────────────────────┐
                   │    RAW SATELLITE DATA   │
                   │   (large `.tif` images) │
                   └────────────┬────────────┘
                                │
                          ┌─────▼─────┐
                          │   SPLIT   │
                          │ Train /   │
                          │ Val / Test│
                          └─────┬─────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     SQUEEZE     │
                       │ e.g Filter out  │
                       │ NoData & clouds │
                       │                 │
                       └────────┬────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │    EXPAND     │
                        │  Rasterize &  │
                        │    Augment    │
                        └───────┬───────┘
                                │
                                ▼          
                        ┌───────────────┐
                        │ FINAL IMAGES  │ 
                        │ (640x640 px)  │
                        └───────┬───────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ LABEL (YOLO only)   │
                     │ Assign bounding box │
                     │ & class labels      │
                     └─────────────────────┘


```

### Imagery

### Limitations

[Chapter 1.](#mad-journal) 
## Project stages

### Lasso

### Dataset creation

### Yolo


