# Jornal for MAD

## Week 1

### Goals
- Make the images used for the ML part easily reproducible.
- Get a lasso regression going for the 12 input variables.
- Use other statistical values to describe the correlation between truth and input variables.
- Plot the findings.
- Do a distinction for different types of images (mines from different regions/seasons).

### Notes
- Reproducibility large issue with R?
    - Check reproducability possibilities for R.
    - Make a python script for the download and provide conda environment.

- Significant difference in convergence speed for normalized datapoints vs raw datapoints
    - Normalization here should be okay as we're mainly interested in the primary contributors and not yet in finding a model to find mining facilities

- Biggest contributor so far seems to be SWIR 1, which seems to be an indicator for heat, which probably is due to the absorption of sunlight by "rock" hence mines.
    - How does this differ for different image types? Forest vs. mining facilities that are not surrounded by trees.
    - Maybe further classify the images into different topological types? Forests, vs, deserts vs prarie etc?
### Progress
