'''
Combines all episode text files from the Desperate Housewives subtitles dataset
into a single text file, with episodes separated by "---".
'''
import os
import re

# Configuration
INPUT_BASE_DIR_NAME = os.path.join("data", "subtitles-text-only", "desperate_housewives")
OUTPUT_FILE_NAME = os.path.join("data", "all_episodes_combined.txt")
EPISODE_SEPARATOR = "\n\n---\n\n"

def extract_season_episode_numbers(filename_basename):
    """
    Extracts season and episode numbers from a filename (e.g., "Desperate.Housewives.S01E02.eng.txt").
    Returns a tuple (season_num, episode_num) for sorting.
    Files not matching the pattern are sorted towards the end.
    """
    match = re.search(r'S(\d+)E(\d+)', filename_basename, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    # Fallback for files not matching the SxxExx pattern, sorts them last
    return (float('inf'), float('inf'))

def get_sorted_season_dirs(root_input_dir):
    """
    Lists and sorts season directories found in the root_input_dir.
    Season directories are expected to be named like "Season 01-text-only".
    """
    season_dirs = []
    if not os.path.isdir(root_input_dir):
        print(f"Error: Input directory '{root_input_dir}' not found.")
        return season_dirs

    for item_name in os.listdir(root_input_dir):
        item_path = os.path.join(root_input_dir, item_name)
        if os.path.isdir(item_path) and item_name.startswith("Season ") and item_name.endswith("-text-only"):
            try:
                # Extract number for sorting (e.g., 1 from "Season 01-text-only")
                season_number = int(item_name.split(' ')[1].split('-')[0])
                season_dirs.append((season_number, item_path))
            except (IndexError, ValueError):
                print(f"Warning: Could not parse season number from directory '{item_name}'. Skipping.")
    
    season_dirs.sort() # Sort by season_number
    return [path for _, path in season_dirs]

def get_sorted_episode_files(season_dir_path):
    """
    Lists and sorts .txt episode files found in a given season directory.
    Sorting is based on season and episode numbers extracted from filenames.
    """
    episode_files = []
    if not os.path.isdir(season_dir_path):
        return episode_files # Should not happen if called correctly

    for item_name in os.listdir(season_dir_path):
        item_path = os.path.join(season_dir_path, item_name)
        # Consider only .txt files that seem to be episode files (containing SxxExx)
        if os.path.isfile(item_path) and item_name.endswith(".txt") and re.search(r'S\d+E\d+', item_name, re.IGNORECASE):
            episode_files.append(item_path)
            
    episode_files.sort(key=lambda f_path: extract_season_episode_numbers(os.path.basename(f_path)))
    return episode_files

def combine_episode_contents(root_input_dir, output_filepath):
    """
    Main function to combine contents of all found episode text files.
    """
    print(f"Starting combination process. Input: '{root_input_dir}', Output: '{output_filepath}'")
    
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory {output_dir}: {e}")
            return

    first_content_written = False
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        season_directories = get_sorted_season_dirs(root_input_dir)

        if not season_directories:
            print(f"No season directories found in '{root_input_dir}'. Output file will be empty.")
            outfile.write("") # Ensure an empty file is created/truncated
            return

        for season_path in season_directories:
            season_name = os.path.basename(season_path)
            print(f"Processing season: {season_name}")
            
            episode_paths = get_sorted_episode_files(season_path)
            if not episode_paths:
                print(f"  No valid episode text files found in {season_name}.")
                continue

            for episode_file_path in episode_paths:
                episode_filename = os.path.basename(episode_file_path)
                season_num, episode_num = extract_season_episode_numbers(episode_filename)
                
                if season_num == float('inf') or episode_num == float('inf'):
                    print(f"  Warning: Could not extract season/episode numbers from '{episode_filename}'. Skipping header for this file.")
                    header = ""
                else:
                    header = f"[Season {season_num:02d} Episode {episode_num:02d}]\n\n"

                try:
                    with open(episode_file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                    
                    if first_content_written: # Add separator before the next episode's content
                        outfile.write(EPISODE_SEPARATOR)
                    
                    outfile.write(header) # Add the episode header
                    outfile.write(content)
                    first_content_written = True 
                    # print(f"    Appended: {episode_filename} with header: S{season_num:02d}E{episode_num:02d}")

                except FileNotFoundError:
                    print(f"  Error: Episode file not found - {episode_file_path}. Skipping.")
                except Exception as e:
                    print(f"  Error processing file {episode_filename}: {e}. Skipping.")
    
    print(f"Successfully combined all episode texts into: {output_filepath}")

if __name__ == "__main__":
    # Assuming the script is run from the root of the workspace.
    workspace_root = os.getcwd()
    
    absolute_input_dir = os.path.join(workspace_root, INPUT_BASE_DIR_NAME)
    absolute_output_file = os.path.join(workspace_root, OUTPUT_FILE_NAME)
    
    combine_episode_contents(absolute_input_dir, absolute_output_file)
