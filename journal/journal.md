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
