import os
import shutil
from pathlib import Path

def rename_and_copy_files(input_dir, output_dir, max_files):
    """
    Copy and rename files from input_dir to output_dir using sequential indices.
    Preserves relationships between .png and .txt files that share the same base name.
    """
    os.makedirs(output_dir, exist_ok=True)
    input_files = list(Path(input_dir).glob('*'))
    file_pairs = {}
    
    # Group files by their base names (everything before the extension)
    for file_path in input_files:
        if file_path.suffix.lower() in ['.png', '.txt']:
            base_name = file_path.stem
            if base_name not in file_pairs:
                file_pairs[base_name] = {'png': None, 'txt': None}
            
            if file_path.suffix.lower() == '.png':
                file_pairs[base_name]['png'] = file_path
            else:
                file_pairs[base_name]['txt'] = file_path
    
    # Copy and rename files, preserving pairs
    idx = 0
    for base_name, files in sorted(file_pairs.items()):
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
            print(f"Warning: Unpaired file found for base name: {base_name}")
        if idx >= max_files:
            break


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
