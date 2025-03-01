import os
import re
from pathlib import Path

def rename_and_process_files(input_dir, max_files):
    """
    Process files in input_dir:
    1. For PNG files, rename them in place
    2. Delete TXT files
    3. Process simple numbered PNG files first, then complex named files
       starting at the next available index (highest simple index + 1)
    """
    input_path = Path(input_dir)
    
    # Step 1: Identify simple numbered PNG files
    simple_png_indices = []
    for file_path in input_path.glob('*.png'):
        if file_path.stem.isdigit():
            simple_png_indices.append(int(file_path.stem))
    
    # Find the highest simple PNG file number
    highest_simple_index = -1
    if simple_png_indices:
        highest_simple_index = max(simple_png_indices)
    
    # Next index for complex files
    next_idx = highest_simple_index + 1
    print(f"Next index for complex files: {next_idx}")
    
    # Step 2: Identify and sort complex pattern PNG files
    complex_pattern_files = []
    for file_path in input_path.glob('*.png'):
        if not file_path.stem.isdigit():  # Skip simple numbered files
            match = re.match(r'iter(\d+)_env(\d+)_step(\d+)_run-id(\d+)', file_path.stem)
            if match:
                iter_num, env_num, step_num, run_id = map(int, match.groups())
                sort_key = (run_id, iter_num, env_num, step_num)
                complex_pattern_files.append((sort_key, file_path))
    
    # Sort complex pattern files
    complex_pattern_files.sort()
    
    # Step 3: Process complex PNG files (rename them)
    processed_count = 0
    for _, file_path in complex_pattern_files:
        new_path = file_path.parent / f"{next_idx}.png"
        file_path.rename(new_path)
        next_idx += 1
        processed_count += 1
        
        if processed_count % 10000 == 0:
            print(f"Renamed {processed_count} PNG files")        
        if processed_count >= max_files:
            break
    
    # Step 4: Delete TXT files
    deleted_count = 0
    for file_path in input_path.glob('*.txt'):
        file_path.unlink()
        deleted_count += 1
    
    print(f"Total: Renamed {processed_count} PNG files, deleted {deleted_count} TXT files")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process files: rename PNGs in place and delete TXTs')
    parser.add_argument('input_dir', help='Directory containing the files to process')
    parser.add_argument('max_files', type=int, help='Maximum number of files to process')
    args = parser.parse_args()
    
    rename_and_process_files(args.input_dir, args.max_files)
    print("Files have been processed successfully!")

if __name__ == "__main__":
    main()
