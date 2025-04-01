import re
import json
# from bs4 import BeautifulSoup
import os

html_file_path = '../topic-modelling/BERTopic/topics_visualization.html'
output_file_path = 'module_terms.txt'

def extract_keywords_from_html_balance(file_path):
    """
    Parses a BERTTopic HTML visualization file using a two-step approach:
    1. Use bracket balancing to reliably isolate the 'customdata' array string.
    2. Apply re.findall for topic entries only within that isolated string.
    """
    all_keywords = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Isolate the customdata array string using bracket balancing
        start_marker = '"customdata"\s*:\s*\['
        start_match = re.search(start_marker, html_content)

        if not start_match:
            print("Error: Could not find the start marker '\"customdata\": ['")
            return None

        # Index of the character *after* the opening bracket '['
        start_index = start_match.end()
        
        balance_counter = 1 
        current_index = start_index
        end_index = -1

        while current_index < len(html_content):
            char = html_content[current_index]
            if char == '[':
                balance_counter += 1
            elif char == ']':
                balance_counter -= 1

            # finding matching closing brac
            if balance_counter == 0:
                end_index = current_index
                break 

            current_index += 1
        if end_index == -1:
            print("Error: Could not find the matching closing bracket for 'customdata' array.")
            return None

        customdata_str = html_content[start_index - 1 : end_index + 1]

        print(f"Successfully isolated the 'customdata' array string using bracket balancing.")
        print(f"Length of captured customdata_str: {len(customdata_str)}")
        print(f"Start of customdata_str:{customdata_str[:200]}...")
        print(f"End of customdata_str:{customdata_str[-200:]}")

        # --- Step 2: Apply findall ONLY to the isolated customdata string ---
        topic_pattern = r'\[\s*(\d+)\s*,\s*"(.*?)"\s*,\s*(\d+)\s*\]'
        topic_matches = re.findall(topic_pattern, customdata_str, re.DOTALL)
        print(f"DEBUG: Number of topic entries found by findall: {len(topic_matches)}")

        if not topic_matches:
            print("If you see this, regex did not work!")
            topic_pattern_flexible = r'\[\s*(\d+)\s*,\s*"(.*?)"\s*,\s*([\d\.]+)\s*\]' # Allow float sizes?
            topic_matches = re.findall(topic_pattern_flexible, customdata_str, re.DOTALL)
            print(f"Topic entries found by findall: {len(topic_matches)}")
            if not topic_matches:
                 print("Regex still could not find topic matches!")
                 return None

        # match processing for topic matching
        processed_count = 0
        for i, topic_match in enumerate(topic_matches):
            try:
                keyword_string = topic_match[1] # Keyword string is the second captured group
                keywords_list = [kw.strip() for kw in keyword_string.split('|')]
                valid_keywords = [kw for kw in keywords_list if kw]
                if valid_keywords:
                    all_keywords.update(valid_keywords)
                    processed_count += 1
            except IndexError:
                 print(f"Warning: Error processing match tuple: {topic_match}. Skipping.")
                 continue
        print(f"Total matches processed where valid keywords were found: {processed_count}")

        if not all_keywords:
            print("Warning: No keywords were extracted.")
            return None

        sorted_keywords = sorted(list(all_keywords))
        return sorted_keywords

    except FileNotFoundError:
        print(f"Error: HTML file not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    print(f"Attempting to parse: {html_file_path}")
    keywords = extract_keywords_from_html_balance(file_path=html_file_path) 
    if keywords:
        print(f"Successfully extracted {len(keywords)} unique keywords.")
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                for keyword in keywords:
                    f_out.write(keyword + '\n')
            print(f"Keywords saved to: {output_file_path}")
        except Exception as e:
            print(f"Error writing keywords to file: {e}")
    else:
        print("Failed to extract keywords.")

