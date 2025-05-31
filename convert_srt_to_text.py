import os
import argparse
import re


def is_sequence_number(line):
    """Check if a line looks like an SRT sequence number."""
    return line.strip().isdigit()


def is_timecode(line):
    """Check if a line looks like an SRT timecode."""
    # Matches lines like: 00:00:16,683 --> 00:00:19,379
    # Allows for slight variations in spacing around -->
    return (
        "-->" in line
        and re.match(
            r"\d{1,2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2},\d{3}", line.strip()
        )
        is not None
    )


def extract_text_from_srt(srt_content):
    """
    Extracts only the subtitle text from SRT formatted string content.
    Skips sequence numbers, timecodes, and blank lines.
    """
    lines = srt_content.splitlines()
    text_lines = []
    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:  # Skip blank lines
            continue
        if is_sequence_number(stripped_line):  # Skip sequence numbers
            continue
        if is_timecode(stripped_line):  # Skip timecodes
            continue

        # If it's not any of the above, it's considered subtitle text
        # Remove HTML tags
        line_without_html = re.sub(r"<[^>]+>", "", stripped_line)
        if (
            line_without_html
        ):  # Only append if the line is not empty after stripping HTML
            text_lines.append(line_without_html)

    return "\n".join(text_lines)


def process_subtitle_file(input_file_path, output_file_path):
    """Reads an SRT file, extracts text, and writes to a new .txt file."""
    try:
        # Try common encodings if utf-8 fails, though utf-8 is standard for .srt
        encodings_to_try = ["utf-8", "latin-1", "windows-1252"]
        content = None
        for enc in encodings_to_try:
            try:
                with open(input_file_path, "r", encoding=enc) as f:
                    content = f.read()
                # print(f"Successfully read {input_file_path} with encoding {enc}")
                break
            except UnicodeDecodeError:
                # print(f"Failed to decode {input_file_path} with {enc}")
                continue

        if content is None:
            print(
                f"Error: Could not decode {input_file_path} with any of the attempted encodings."
            )
            return False

        text_content = extract_text_from_srt(content)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        return True
    except Exception as e:
        print(f"Error processing file {input_file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert SRT subtitle files to text-only (.txt) files, preserving directory structure and modifying season folder names."
    )
    parser.add_argument(
        "input_base_dir",
        help="Base input directory that contains the specific show's subtitle folder. E.g., if subtitles are in 'data/subtitles/desperate_housewives', pass 'data/subtitles'.",
    )
    parser.add_argument(
        "output_base_dir",
        help="Base output directory where the text-only subtitles for the show will be saved. E.g., 'data/subtitles-text-only'. The script will create a 'desperate_housewives' subfolder here.",
    )
    parser.add_argument(
        "--show_folder_name",
        default="desperate_housewives",
        help="Name of the show's folder within the input_base_dir (and to be created in output_base_dir). Default: 'desperate_housewives'.",
    )

    args = parser.parse_args()

    input_show_directory = os.path.join(args.input_base_dir, args.show_folder_name)
    output_show_directory = os.path.join(args.output_base_dir, args.show_folder_name)

    if not os.path.isdir(input_show_directory):
        print(
            f"Error: Input show directory not found: {os.path.abspath(input_show_directory)}"
        )
        return

    print(f"Starting SRT to text conversion for '{args.show_folder_name}'...")
    print(f"Reading from: {os.path.abspath(input_show_directory)}")
    print(f"Writing to: {os.path.abspath(output_show_directory)}")

    processed_count = 0
    failed_count = 0

    for root, _, files in os.walk(input_show_directory):
        for filename in files:
            if filename.lower().endswith(".srt"):
                input_srt_file_path = os.path.join(root, filename)

                # Determine the relative path from the input_show_directory
                # e.g., "Season 01/EpisodeFile.eng.srt"
                relative_path_to_srt = os.path.relpath(
                    input_srt_file_path, input_show_directory
                )

                # Split the relative path into components
                path_components = []
                temp_path = relative_path_to_srt
                while True:
                    temp_path, tail = os.path.split(temp_path)
                    if tail:  # tail is a component (file or dir name)
                        path_components.insert(0, tail)
                    if (
                        not temp_path or temp_path == os.sep
                    ):  # Reached the top of the relative path
                        break

                # Change file extension from .srt to .txt
                output_filename_txt = os.path.splitext(path_components[-1])[0] + ".txt"
                path_components[-1] = output_filename_txt

                # Modify season folder name if present (e.g., "Season 01" -> "Season 01-text-only")
                if len(path_components) > 1 and path_components[0].lower().startswith(
                    "season"
                ):
                    path_components[0] = f"{path_components[0]}-text-only"

                # Construct the final output path
                output_txt_relative_path = os.path.join(*path_components)
                final_output_txt_path = os.path.join(
                    output_show_directory, output_txt_relative_path
                )

                if process_subtitle_file(input_srt_file_path, final_output_txt_path):
                    processed_count += 1
                else:
                    failed_count += 1

    print(f"\nConversion finished.")
    print(f"Successfully processed: {processed_count} files.")
    if failed_count > 0:
        print(f"Failed to process: {failed_count} files.")


if __name__ == "__main__":
    main()
