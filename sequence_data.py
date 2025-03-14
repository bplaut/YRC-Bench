import os
import shutil
import re
from pathlib import Path

def rename_and_copy_files(input_dir, output_dir, start_idx, end_idx):
    """
    Copy and rename PNG files from input_dir to output_dir using sequential indices.
    Processes files from start_idx (inclusive) to end_idx (exclusive).
    Sorts files by run-id, iter, env, and step.
    """
    os.makedirs(output_dir, exist_ok=True)
    input_files = list(Path(input_dir).glob('*.png'))
    file_pairs = {}

    # Group PNG files by the parsed values from the filename
    for file_path in input_files:
        base_name = file_path.stem
        
        # Extract iter, env, step, and run-id using regex
        match = re.match(r'iter(\d+)_env(\d+)_step(\d+)_run-id(\d+)', base_name)
        if match:
            iter_num, env_num, step_num, run_id = map(int, match.groups())
            
            # Use a tuple as a key for sorting: (run_id, iter, env, step)
            sort_key = (run_id, iter_num, env_num, step_num)
            file_pairs[sort_key] = file_path
    
    # Copy and rename files
    idx = 0
    num_processed = 0
    for sort_key, file_path in sorted(file_pairs.items()):
        if start_idx <= idx < end_idx:
            new_name = os.path.join(output_dir, f"{idx}.png")
            shutil.copy2(file_path, new_name)
            num_processed += 1
            
            if num_processed % 10000 == 0:
                print(f"Processed {idx} files")
        
        idx += 1

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Rename and copy PNG files with sequential indices')
    parser.add_argument('input_dir', help='Input directory containing the original files')
    parser.add_argument('output_dir', help='Output directory for the renamed files')
    parser.add_argument('start_idx', type=int, help='Starting index (inclusive)')
    parser.add_argument('end_idx', type=int, help='Ending index (exclusive)')
    args = parser.parse_args()
    
    rename_and_copy_files(args.input_dir, args.output_dir, args.start_idx, args.end_idx)
    print("Files have been copied and renamed successfully!")

if __name__ == "__main__":
    main()
