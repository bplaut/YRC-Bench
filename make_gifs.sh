#!/bin/bash

# Read the first argument: num environments
num_envs=$1

python group_images_by_env.py data/coinrun gifs/coinrun $num_envs gifs/coinrun.tex
python group_images_by_env.py data/coinrun_aisc gifs/coinrun_aisc $num_envs gifs/coinrun_aisc.tex
python group_images_by_env.py data/maze gifs/maze $num_envs gifs/maze.tex
python group_images_by_env.py data/maze_aisc gifs/maze_aisc $num_envs gifs/maze_aisc.tex
zip -r gifs.zip gifs
