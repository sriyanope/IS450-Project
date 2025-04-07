import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
# import csv 

INPUT_CSV_DIR = './output/nodes-and-edges/'

OUTPUT_IMG_DIR = './output/network-x-imgs/'

MODEL_NAMES = [
    'claude-sonnet',
    'gpt-4o',
    'llama3',
    'deepseek-r1'
]


def create_and_save_network_visualization(nodes_csv_path, edges_csv_path, output_image_path, model_name):
    """
    Reads node/edge CSVs, generates NetworkX visualization, and saves it.
    """
    print(f"--- Processing Model: {model_name} ---")
    print(f"Loading data from:\n Nodes: {nodes_csv_path}\n Edges: {edges_csv_path}")

    # 1. Load Data
    try:
        nodes_df = pd.read_csv(nodes_csv_path)
        edges_df = pd.read_csv(edges_csv_path)
        if not {'Id', 'Label', 'Type'}.issubset(nodes_df.columns):
             raise ValueError("Nodes CSV must contain 'Id', 'Label', 'Type' columns.")
        if not {'Source', 'Target'}.issubset(edges_df.columns):
             raise ValueError("Edges CSV must contain 'Source', 'Target' columns.")
    except FileNotFoundError:
        print(f"Error: Skipping {model_name}. Cannot find required CSV files.")
        print(f" Checked: {nodes_csv_path}")
        print(f" Checked: {edges_csv_path}")
        return # Skip to next model if files not found
    except Exception as e:
        print(f"Error loading CSV files for {model_name}: {e}")
        return

    # 2. Create NetworkX Graph
    G = nx.Graph()
    for index, row in nodes_df.iterrows():
        G.add_node(str(row['Id']), label=str(row['Label']), type=str(row['Type']))
    edges_df['Source'] = edges_df['Source'].astype(str)
    edges_df['Target'] = edges_df['Target'].astype(str)
    G.add_edges_from(edges_df[['Source', 'Target']].values)
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # 3. Prepare Visual Properties
    # print("Calculating layout...")
    # k_val = 0.3 / math.sqrt(G.number_of_nodes()) if G.number_of_nodes() > 0 else 0.1
    # try:
    #     pos = nx.spring_layout(G, k=k_val, iterations=50, seed=42)
    #     print("Layout calculated.")
    # except Exception as e:
    #      print(f"Error during layout calculation: {e}. Using random layout.")
    #      pos = nx.random_layout(G, seed=42)
    print("Calculating Kamada-Kawai layout...")
    try:
        pos = nx.kamada_kawai_layout(G)
        print("Layout calculated.")
    except Exception as e: 
        # Fallback if kamada_kawai fails
        print(f"Kamada-Kawai failed: {e}. Using spring_layout as fallback.")
        k_val = 0.5 / math.sqrt(G.number_of_nodes()) if G.number_of_nodes() > 0 else 0.1
        pos = nx.spring_layout(G, k=k_val, iterations=75, seed=42)

    color_map = {'Main Topic': 'skyblue', 'Subtopic': 'lightgreen', 'Unmapped': 'salmon'}
    node_colors = [color_map.get(G.nodes[node].get('type', 'Unknown'), 'gray') for node in G.nodes()]

    degrees = dict(G.degree())
    min_size = 100
    max_size = 1500
    size_factor = 30
    node_sizes = [min(min_size + degrees.get(node, 0) * size_factor, max_size) for node in G.nodes()]

    labels = {node: G.nodes[node].get('label', node) for node in G.nodes()}

    # 4. Draw Graph
    print("Drawing graph...")
    plt.figure(figsize=(25, 25))
    nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color="gray")
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_color="black")
    plt.title(f"Concept Map Visualization ({model_name})", size=20)
    plt.axis('off')

    # 5. Save Plot
    try:
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, format="png", dpi=300, bbox_inches="tight")
        print(f"Graph saved successfully to: {output_image_path}")
    except Exception as e:
        print(f"Error saving graph image to {output_image_path}: {e}")
    
    plt.close() 



if __name__ == "__main__":
    print("Starting batch visualization generation...")
    if not os.path.exists(OUTPUT_IMG_DIR):
        print(f"Creating output image directory: {OUTPUT_IMG_DIR}")
        os.makedirs(OUTPUT_IMG_DIR)

    for model_name in MODEL_NAMES:
        nodes_file = os.path.join(INPUT_CSV_DIR, f"{model_name}_nodes.csv")
        edges_file = os.path.join(INPUT_CSV_DIR, f"{model_name}_edges.csv")
        output_file = os.path.join(OUTPUT_IMG_DIR, f"{model_name}_network.png")
        create_and_save_network_visualization(nodes_file, edges_file, output_file, model_name)

    print("Batch visualization generation finished.")