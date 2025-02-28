import os
import shutil
import re
from pathlib import Path

def rename_and_copy_files(input_dir, output_dir, max_files):
    """
    Copy and rename files from input_dir to output_dir using sequential indices.
    Preserves relationships between .png and .txt files that share the same base name.
    Sorts files by run-id, iter, env, and step.
    """
    os.makedirs(output_dir, exist_ok=True)
    input_files = list(Path(input_dir).glob('*'))
    file_pairs = {}

    # Group files by the parsed values from the filename
    for file_path in input_files:
        if file_path.suffix.lower() in ['.png', '.txt']:
            base_name = file_path.stem
            
            # Extract iter, env, step, and run-id using regex
            match = re.match(r'iter(\d+)_env(\d+)_step(\d+)_run-id(\d+)', base_name)
            if match:
                iter_num, env_num, step_num, run_id = map(int, match.groups())
                
                # Use a tuple as a key for sorting: (run_id, iter, env, step)
                sort_key = (run_id, iter_num, env_num, step_num)
                
                if sort_key not in file_pairs:
                    file_pairs[sort_key] = {'png': None, 'txt': None}
                
                if file_path.suffix.lower() == '.png':
                    file_pairs[sort_key]['png'] = file_path
                else:
                    file_pairs[sort_key]['txt'] = file_path
    
    # Copy and rename files, preserving pairs
    missing_txt_count = 0
    idx = 0
    for sort_key, files in sorted(file_pairs.items()):
        # Only process if we have both png and txt files
        if files['png'] and files['txt']:
            # Copy PNG file
            png_new_name = os.path.join(output_dir, f"{idx}.png")
            shutil.copy2(files['png'], png_new_name)
            
            # Copy corresponding TXT file
            txt_new_name = os.path.join(output_dir, f"{idx}.txt")
            shutil.copy2(files['txt'], txt_new_name)
            
            idx += 1
            if idx % 10000 == 0:
                print(f"Processed {idx} files")
        else:
            run_id, iter_num, env_num, step_num = sort_key
            missing_txt_count += 1
        
        if idx >= max_files:
            break
    print(f"Found {missing_txt_count} files without a matching .txt file")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Rename and copy files with sequential indices')
    parser.add_argument('input_dir', help='Input directory containing the original files')
    parser.add_argument('output_dir', help='Output directory for the renamed files')
    parser.add_argument('max_files', type=int, help='Maximum number of files to process')
    args = parser.parse_args()
    
    rename_and_copy_files(args.input_dir, args.output_dir, args.max_files)
    print("Files have been copied and renamed successfully!")

if __name__ == "__main__":
    main()
