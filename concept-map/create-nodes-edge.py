import json
import pandas as pd
import os
import argparse
import csv 

def process_llm_json(json_file_path, output_dir=None):
    """
    Processes an LLM output JSON file containing a concept map structure
    and generates nodes.csv and edges.csv files.

    Args:
        json_file_path (str): Path to the input JSON file.
        output_dir (str, optional): Directory to save the output CSV files.
                                     If None, saves in the same dir as the input JSON.
    """
    print(f"Processing file: {json_file_path}")

    # load json data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{json_file_path}'")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON file '{json_file_path}'. Invalid JSON: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred loading the file: {e}")
        return

    # extract data and build node edge set
    nodes = {} 
    edges = set() 

    # Process conceptMap
    if 'conceptMap' in data and isinstance(data['conceptMap'], list):
        for item in data['conceptMap']:
            if 'topic' in item and 'subtopics' in item and isinstance(item['subtopics'], list):
                main_topic = item['topic'].strip()
                if main_topic:
                    # Add/update main topic node type
                    nodes[main_topic] = 'Main Topic'
                    
                    for subtopic in item['subtopics']:
                        subtopic_clean = subtopic.strip()
                        if subtopic_clean:
                             # Add/update subtopic node type (might override if it was unmapped)
                             # Prioritize 'Subtopic' type if seen here
                             if subtopic_clean not in nodes or nodes[subtopic_clean] == 'Unmapped':
                                nodes[subtopic_clean] = 'Subtopic'
                             # Add edge
                             edges.add((main_topic, subtopic_clean))
            else:
                print("Warning: Found item in 'conceptMap' without 'topic' or 'subtopics' list.")
    else:
        print("Warning: 'conceptMap' key not found or is not a list in the JSON.")

    # Process unmappedTerms
    if 'unmappedTerms' in data and isinstance(data['unmappedTerms'], list):
        for term in data['unmappedTerms']:
            term_clean = term.strip()
            if term_clean:
                # Add as unmapped only if not already added as main/subtopic
                if term_clean not in nodes:
                    nodes[term_clean] = 'Unmapped'
    else:
        print("Warning: 'unmappedTerms' key not found or is not a list in the JSON.")
        

    
    # Nodes DataFrame
    node_list_for_df = []
    for node_id, node_type in nodes.items():
        node_list_for_df.append({'Id': node_id, 'Label': node_id, 'Type': node_type})
        
    if not node_list_for_df:
        print("Error: No nodes extracted. Cannot create node file.")
        return
        
    nodes_df = pd.DataFrame(node_list_for_df)
    print(f"Created DataFrame with {len(nodes_df)} nodes.")

    # Edges DataFrame
    if not edges:
        print("Warning: No edges extracted. Edge file will be empty or not created.")
        edges_df = pd.DataFrame(columns=['Source', 'Target', 'Type', 'Weight']) # Create empty df
    else:
        edge_list_for_df = [{'Source': source, 'Target': target, 'Type': 'Undirected', 'Weight': 1.0} 
                           for source, target in edges]
        edges_df = pd.DataFrame(edge_list_for_df)
        print(f"Created DataFrame with {len(edges_df)} edges.")

    # Output path for mapping
    if output_dir is None:
        output_dir = os.path.dirname(json_file_path) 
    
    # Ensure output directory exists
    if output_dir and not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
        
    base_name = os.path.basename(json_file_path)
    file_prefix = os.path.splitext(base_name)[0] 
    
    nodes_csv_path = os.path.join(output_dir, f"{file_prefix}_nodes.csv")
    edges_csv_path = os.path.join(output_dir, f"{file_prefix}_edges.csv")

    # Save DataFrames to CSV
    try:
        # Use QUOTE_ALL for safety if labels contain commas/quotes
        nodes_df.to_csv(nodes_csv_path, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
        print(f"Nodes saved to: {nodes_csv_path}")
        
        edges_df.to_csv(edges_csv_path, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
        print(f"Edges saved to: {edges_csv_path}")
        
    except Exception as e:
        print(f"Error saving CSV files: {e}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process LLM JSON output to generate node and edge CSV files for Gephi.")
    parser.add_argument("json_file", help="Path to the input JSON file from the LLM.")
    parser.add_argument("-o", "--output_dir", help="Directory to save the output CSV files (defaults to input file's directory).", default=None)
    
    args = parser.parse_args()
    
    # Check if input file exists before processing
    if not os.path.isfile(args.json_file):
         print(f"Error: Input file not found: {args.json_file}")
    else:
        process_llm_json(args.json_file, args.output_dir)