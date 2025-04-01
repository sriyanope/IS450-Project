import os
import glob
import re

program_files_dir = '../topic-modelling/corpus' 
FILE_PATTERN = 'program*.txt'
output_file_path = './data/course_topics.txt' 

def extract_course_titles(directory, pattern):
    """
    Extracts potential course titles from program text files.
    directory - the directory containing the text files.
    pattern - the filename pattern to search for (e.g., 'program*.txt').

    output: A sorted list of unique potential course titles found in the files.
    """
    unique_titles = set()
    search_path = os.path.join(directory, pattern)
    file_paths = glob.glob(search_path)

    if not file_paths:
        print(f"Error: No files found matching pattern '{pattern}' in directory '{directory}'")
        return None
    # print('hello')
    print(f"Found {len(file_paths)} files to process...")

    # Regex to find content immediately following <DOC> tag, assuming title is the first non-empty line.
    # - <DOC>\s*: Matches '<DOC>' followed by optional whitespace (including newlines)
    # - ([^\n<]+): Captures Group 1: one or more characters that are NOT a newline (\n) or '<'
    #   (to avoid capturing the next tag immediately)
    # - \n?: Optionally matches a newline after the title.
    # re.IGNORECASE: Makes <DOC> case-insensitive if needed
    title_regex = re.compile(r"<DOC>\s*([^\n<]+)", re.IGNORECASE)

    for file_path in file_paths:
        # print(f"Processing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = title_regex.findall(content)
            
            for title in matches:
                cleaned_title = title.strip()
                if len(cleaned_title) > 3 and '<' not in cleaned_title:
                     unique_titles.add(cleaned_title)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    if not unique_titles:
         print("Warning: No potential titles were extracted.")
         return []
    return sorted(list(unique_titles))


if __name__ == "__main__":
    print(f"Starting title extraction from: {program_files_dir}")
    titles = extract_course_titles(program_files_dir, FILE_PATTERN)

    if titles is not None:
        print(f"Extracted {len(titles)} unique potential course titles.")
        output_dir = os.path.dirname(output_file_path)

        if output_dir and not os.path.exists(output_dir):
             print(f"Creating output directory: {output_dir}")
             os.makedirs(output_dir)
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                for title in titles:
                    f_out.write(title + '\n')
            print(f"Course titles saved to: {output_file_path}")
        except Exception as e:
            print(f"Error writing titles to file '{output_file_path}': {e}")
    else:
        print("Title extraction failed.")