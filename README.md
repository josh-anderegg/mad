# MAD journal

## Overarching goals
1.  Provide a lightweight model for classification, since we expect that it will take huge computing resources to scan the whole world.
2.  Images have up to 12 channels. Tell us whether there is a combination of channels which can enhance the identification of mines. This is essentially a preprocessing step/possible enhancement for the object detection models.
3. Once the optimal combo of channel identify, you can implement the transformation on Sentinel2 imagery in GEE and deploy a classification algorithm (either supervised or unsupervised) on the transformed imagery to identify mining assets.

## Week 1

### Goals
- [x] Get a lasso regression to work for the 12 bands.
- [x] From the lass regression determine the most important bands.
- [x] Plot the findings.
- [ ] Research differences between lasso results based on other variables like mine types (evaporation ponds, open mines, urban ones, quarries).

### Notes
- Reproducibility large issue with R?
    - Check reproducability possibilities for R.
    - Make a python script for the download and provide conda environment (maybe even docker container to easily reproduce set directly).

- Datapoints (bands) in satellite imagery have different orders of values.
    - ![GEE bands ranges](/journal/GEE-bands.png).
    - ![GEE average bands for Switzerland](/journal/GEE-average-channels.png)
    - Normalization here should be okay as we're mainly interested in the primary contributors and not yet in finding a model to find mining facilities.
        - It should also significantly speed up the convergence for lasso.
- Is the GEE scripts actually correct? 
    - ![this GEE output](/journal/GEE-output.png)
    - Wouldn't we expect all the surrounding negative squares to be extracted (red)?
- Biggest contributor so far seems to be SWIR 1, which seems to be an indicator for heat, which probably is due to the absorption of sunlight by "rock" hence mines.
    - How does this differ for different image types? Forest vs. mining facilities that are not surrounded by trees.
    - Maybe further classify the images into different topological types? Forests, vs, deserts vs prarie etc?

### Problems
- Currently I only take in single images (or multiple of them) to perform the lasso regression. To have a less biased input, I would need to perform lasso regression over all of the images which should not be possible due to memory constraints.
    - **Solution**: From all images in the test set, select a random (predictably) subset. Potential issue here is that there will be only a small amount of them actually being a mine pixel
- The classification with Lasso will most probably be to imprecise.
    - **Solution**: Try to improve the precision of lasso by excluding certain pixels from the learning dataset (like Marc proposed, ones with larger distance to the polygon edge), alternatively instead of lasso learning a binary assignment is mine or not, have it learn a probability (based on gaussing the input)
    - **Solution**: Consider a more intricate pipeline that combines visual computing techniques (Mainly SIFT) with object detection ML tools.

 

