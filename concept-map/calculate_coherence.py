import json
import pandas as pd
import os
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore") 

def calculate_topic_coherence(json_file_path, model_name='all-MiniLM-L6-v2'):
    """
    Calculates an adapted topic coherence score for an LLM's concept map.
    The score is the average of mean pairwise cosine similarities for subtopics within each main topic group.

    Args:
        json_file_path (str): Path to the input LLM JSON file.
        model_name (str): Name of the sentence-transformer model to use for embeddings.

    Returns:
        float: The overall coherence score, or None if calculation fails.
    """
    print(f"\n--- Calculating Coherence for: {os.path.basename(json_file_path)} ---")

    # Load JSON Data ---
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file_path}': {e}")
        return None

    # Load Sentence Transformer Model 
    try:
        print(f"Loading sentence transformer model: {model_name}...")
        # Load model (will download on first run)
        embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", token=False)
        print("Model loaded.")
    except Exception as e:
        print(f"Error loading sentence transformer model '{model_name}': {e}")
        return None

    # Calculate Coherence for Each Group 
    group_coherence_scores = []
    total_subtopics_processed = 0
    groups_processed = 0

    if 'conceptMap' not in data or not isinstance(data['conceptMap'], list):
        print("Error: 'conceptMap' key not found or is not a list.")
        return None

    for item in data['conceptMap']:
        if 'topic' in item and 'subtopics' in item and isinstance(item['subtopics'], list):
            main_topic = item['topic']
            subtopics = [st.strip() for st in item['subtopics'] if st.strip()] # Cleaned list

            if len(subtopics) > 1: # Need at least 2 subtopics to calculate pairwise similarity
                groups_processed += 1
                total_subtopics_processed += len(subtopics)
                try:
                    # Generate embeddings
                    embeddings = embedder.encode(subtopics, show_progress_bar=False)

                    # Calculate pairwise cosine similarity matrix
                    sim_matrix = cosine_similarity(embeddings)

                    # Calculate average similarity (excluding diagonal, averaging upper triangle)
                    # Get indices of the upper triangle (excluding diagonal k=1)
                    indices = np.triu_indices_from(sim_matrix, k=1)
                    if len(indices[0]) > 0: # Ensure there are pairs
                      group_avg_similarity = np.mean(sim_matrix[indices])
                      group_coherence_scores.append(group_avg_similarity)
                      # print(f" Coherence for '{main_topic}' ({len(subtopics)} terms): {group_avg_similarity:.4f}")
                    else: 
                       print(f"  Warning: No pairs found for similarity in group '{main_topic}' despite >1 subtopic.")
                       
                except Exception as e:
                    print(f"Error calculating coherence for topic '{main_topic}': {e}")
            # else:
            #     print(f" Skipping coherence for '{main_topic}': Only {len(subtopics)} subtopic(s).")

    # Calculate Overall Score 
    if not group_coherence_scores:
        print("Error: No topic groups with >1 subtopic found. Cannot calculate overall coherence.")
        return None

    overall_coherence = np.mean(group_coherence_scores)
    print(f"\nProcessed {groups_processed} topic groups with >1 subtopic.")
    print(f"Total subtopics included in calculation: {total_subtopics_processed}")
    print(f"Overall Average Group Coherence: {overall_coherence:.4f}")

    return overall_coherence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate adapted topic coherence for LLM JSON output.")
    parser.add_argument("json_file", help="Path to the input JSON file from the LLM.")

    args = parser.parse_args()

    if not os.path.isfile(args.json_file):
         print(f"Error: Input file not found: {args.json_file}")
    else:
        score = calculate_topic_coherence(args.json_file)
        if score is not None:
             print(f"\nFinal Coherence Score for {args.json_file}: {score:.4f}")
        else:
             print(f"\nFailed to calculate coherence score for {args.json_file}.")