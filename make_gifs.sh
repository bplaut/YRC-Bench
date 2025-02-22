#!/bin/bash

# Read the first argument: num environments
num_envs=$1

python collect_images.py data/coinrun/images gifs/normal $num_envs gifs/normal.tex
python collect_images.py data/coinrun_aisc/images gifs/aisc $num_envs gifs/aisc.tex
zip -r gifs.zip gifs
