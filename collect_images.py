import os
import sys
import re
from pathlib import Path
import shutil

def parse_filename(filename):
    """Parse iteration, environment, step, and run-id from filename."""
    match = re.match(r'iter(\d+)_env(\d+)_step(\d+)_run-id(\d+)\.png', filename)
    if not match:
        return None
    return {
        'iter': int(match.group(1)),
        'env': int(match.group(2)),
        'step': int(match.group(3)),
        'run_id': int(match.group(4))
    }

def get_env_mapping(input_dir, num_envs):
    """Create mapping from (iter, env, run_id) to new env number."""
    files = [f for f in os.listdir(input_dir) if f.endswith('.png')]
    unique_envs = set()
    
    for f in files:
        parsed = parse_filename(f)
        if parsed:
            unique_envs.add((parsed['run_id'], parsed['iter'], parsed['env']))
    
    # Only take up to num_envs environments
    sorted_envs = sorted(unique_envs)
    return {env: idx for idx, env in enumerate(sorted_envs[:num_envs])}

def process_files(input_dir, output_dir, num_envs):
    """Process files and return maximum steps per environment."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    env_mapping = get_env_mapping(input_dir, num_envs)
    max_steps = {}  # Track maximum step number for each new environment
    
    # Process each file
    for file in input_dir.glob('*.png'):
        parsed = parse_filename(file.name)
        if not parsed:
            continue
            
        old_env_key = (parsed['run_id'], parsed['iter'], parsed['env'])
        if old_env_key not in env_mapping:
            continue  # Skip environments beyond num_envs
            
        new_env = env_mapping[old_env_key]
        step = parsed['step']
        
        # Track maximum step for each environment
        max_steps[new_env] = max(max_steps.get(new_env, 0), step)
        
        # Create new filename and copy file
        new_filename = f"env{new_env}_step{step}.png"
        shutil.copy2(file, output_dir / new_filename)
    
    return max_steps

def generate_latex(tex_filepath, max_steps, num_envs, output_dir):
    """Generate LaTeX beamer presentation."""
    latex_content = r"""
\documentclass[pdf]{beamer}
\usepackage[utf8]{inputenc}
\usepackage{gensymb}
\usepackage{amsmath,amsfonts}
\usepackage{graphicx}
\usepackage{pgfplots}
\usepackage{tikz}
\usepackage{mathtools}
\usepackage{amsthm}
\usetikzlibrary{arrows}
\usepackage{nccmath}
\usepackage[percent]{overpic}
\usepackage{rotating}
\usepackage{array, booktabs}
\usepackage{centernot}
\usepackage{animate}
\usepackage[absolute,overlay]{textpos}
% Begin tikz
\usepackage{pgf}
\usetikzlibrary{shadows,arrows,decorations,decorations.shapes,backgrounds,shapes,snakes,automata,fit,petri,shapes.multipart,calc,positioning,shapes.geometric,graphs,graphs.standard}
% End tikz
% for checkmark and xmarks
\usepackage{pifont}% http://ctan.org/pkg/pifont
\newcommand{\cmark}{\ding{51}}%
\newcommand{\xmark}{\ding{55}}%
\newcommand\figscale{0.74}
\mode<presentation>{}
\setlength{\fboxrule}{2pt}
%gets rid of bottom navigation symbols
\beamertemplatenavigationsymbolsempty
\setbeamertemplate{page number in head/foot}{}
%gets rid of footer
%will override 'frame number' instruction above
%comment out to revert to previous/default definitions
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\E}{\mathbb{E}}
\newcommand{\bbrpos}{\mathbb{R}_{\ge 0}}
\newcommand\bbr{\mathbb{R}}
\newcommand{\todo}[1]{{\color{red} todo: #1}}
\begin{document}
\newcommand\fps{15}
"""
    
    # Add frames for each environment
    last_dir = Path(output_dir).name
    for env in range(num_envs):
        file_prefix = f"{last_dir}/env{env}_step"
        if env not in max_steps:
            continue  # Skip if we don't have any files for this environment
        frame = f"""
\\begin{{frame}}{{Env {env}}}
\\begin{{center}}
\\animategraphics[loop,controls,autoplay,width=3 in]{{\\fps}}{{{file_prefix}}}{{0}}{{{max_steps[env]}}}
\\end{{center}}
\\end{{frame}}
"""
        latex_content += frame
    
    latex_content += "\n\\end{document}"
    
    # Create directory if it doesn't exist
    tex_filepath = Path(tex_filepath)
    tex_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(tex_filepath, 'w') as f:
        f.write(latex_content.strip())

def main():
    if len(sys.argv) != 5:
        print("Usage: python collect_images.py input_dir output_dir num_envs tex_filepath")
        sys.exit(1)
        
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    num_envs = int(sys.argv[3])
    tex_filepath = sys.argv[4]
    
    try:
        max_steps = process_files(input_dir, output_dir, num_envs)
        generate_latex(tex_filepath, max_steps, num_envs, output_dir)
        print(f"Successfully processed files in {output_dir} and generated LaTeX presentation at {tex_filepath}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
