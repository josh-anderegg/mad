#!/bin/bash

# Replace 'your_script.py' with the actual name of your Python script
for i in {1..50}
do
    echo "Run #$i"
    ../lasso_on_tif0613.py data/train/* -v -c 100 -p 8000
done