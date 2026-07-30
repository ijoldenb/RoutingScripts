from pathlib import Path
import networkx as nx
import random
import yaml

import yaml

with open("sim_ip.yaml", "r") as f:
    config = yaml.safe_load(f)
sim_data = config.get("sim_ip", config) if isinstance(config, dict) else config
numNodes = len(sim_data)

def generate_satellite_topology(num_nodes=numNodes, timestamp=0.0):
    # 1. Initialize an Undirected Graph (perfect for symmetric links)
    G = nx.Graph()
    
    # 2. Add your nodes (remains 0-indexed internally for NetworkX efficiency)
    G.add_nodes_from(range(num_nodes))
    
    # 3. Create edges with custom metrics (Symmetric by default in nx.Graph)
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Simulated orbital logic
            simulated_bandwidth = round(random.uniform(2.0, 10.0), 2)  # Mbps
            simulated_loss = round(random.uniform(0.0, 0.05), 4)       # Drop rate
            simulated_latency = round(random.uniform(10.0, 150.0), 2)  # Latency in ms
            
            # Add edge with properties
            G.add_edge(i, j, bandwidth=simulated_bandwidth, loss=simulated_loss, latency=simulated_latency)
            
    return G

def export_to_ns3_trace(filename, snapshots):
    # Generate the topology_trace.yaml file
    with open(filename, 'w') as f:
        # Sort the timestamps to ensure chronological order
        for timestamp, graph in sorted(snapshots.items()):
            f.write(f"- time: {float(timestamp)}\n")
            f.write(f"  links:\n")
            
            for src, dst, data in graph.edges(data=True):
                bw = data['bandwidth']
                loss = data['loss']
                lat = data['latency']
                
                # --- Shift 0-indexed nodes to 1-indexed for the YAML file ---
                f.write(f"    - src: {int(src) + 1}\n")
                f.write(f"      dst: {int(dst) + 1}\n")
                f.write(f"      bw: {float(bw)}\n")
                f.write(f"      drop: {float(loss)}\n")
                f.write(f"      latency: {float(lat)}\n")
                
    print(f"Successfully generated 1-indexed trace at: {filename}")

# Simulate a 1-hour window with updates every 30 seconds
simLength = 1 * 3600  # Simulation Duration in Seconds
simStep = 30          # Output every 30 seconds
snapshots = {}

for x in range(0, simLength + 1, simStep):
    snapshots[x] = generate_satellite_topology(numNodes, x)
    
filePath = Path("/home/ijoldenb/ns-3.48/scratch/topology_trace.yaml")
    
export_to_ns3_trace(filePath, snapshots)
print("NetworkX topology trace exported successfully!")