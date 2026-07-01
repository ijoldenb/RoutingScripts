from pathlib import Path

import networkx as nx
import random

numNodes = 3; 

def generate_satellite_topology(num_nodes=numNodes, timestamp=0.0):
    # 1. Initialize an Undirected Graph (perfect for symmetric links)
    G = nx.Graph()
    
    # 2. Add your nodes
    G.add_nodes_from(range(num_nodes))
    
    # 3. Create edges with custom metrics (Symmetric by default in nx.Graph)
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Simulated orbital logic (replace with your Hypatia math later)
            simulated_bandwidth = round(random.uniform(2.0, 10.0), 2)  # Mbps
            simulated_loss = round(random.uniform(0.0, 0.03), 4)       # Drop rate
            
            # Add edge with properties
            G.add_edge(i, j, bandwidth=simulated_bandwidth, loss=simulated_loss)
            
    return G

def export_to_ns3_trace(filename, snapshots):
    with open(filename, 'w') as f:
        for timestamp, graph in snapshots.items():
            f.write(f"TIMESTAMP {timestamp}\n")
            f.write("# src dst bandwidth_mbps loss_rate\n")
            
            # NetworkX makes iterating over unique edges trivial
            for src, dst, data in graph.edges(data=True):
                bw = data['bandwidth']
                loss = data['loss']
                f.write(f"{src} {dst} {bw} {loss}\n")
                
            f.write("END\n\n")

# Simulate a 1-hour window with updates every 5 seconds
simLength = 1*3600  # Simulation Duration in Seconds
simStep = 5  # Output every 5 seconds
snapshots = {}

for x in range(0, simLength + 1, simStep):
    snapshots[x] = generate_satellite_topology(numNodes, x)
    
filePath = Path("/Users/iolde/iCloud/iCloudDrive/School/Research/DrGeordon/Programs/ns-3.48/scratch/topology_trace.txt")
    
export_to_ns3_trace(filePath, snapshots)
print("NetworkX topology trace exported successfully!")