#!/bin/bash

# Read the first argument: num environments
num_envs=$1

python group_images_by_env.py data/coinrun/images gifs/normal $num_envs gifs/normal.tex
python group_images_by_env.py data/coinrun_aisc/images gifs/aisc $num_envs gifs/aisc.tex
zip -r gifs.zip gifs
