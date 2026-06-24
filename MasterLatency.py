import socket
import json
import time

# Dictionary mapping Pi numbers to their actual testbed IP addresses
PI_CLUSTER = {
    1: "10.0.0.11",
    2: "10.0.0.12",
    3: "10.0.0.13",
    # ... up to Pi 20
}

UDP_PORT = 5005
PHYSICAL_BASELINE_OVERHEAD = 0.5  # 0.5ms subtracted to account for the Aruba 2920 switch & cabling

def calculate_orbital_latencies(sim_step):
    """
    Mock function representing your orbital mechanics engine.
    Returns a multi-dimensional dictionary mapping source PIs to target PIs and distances.
    """
    # Example state for Simulation Step X:
    # Pi 1 can talk to Pi 2 (120ms distance) and Pi 3 (45ms distance)
    # This matrix naturally changes as your simulation step increments
    matrix = {
        1: {PI_CLUSTER[2]: 120.0, PI_CLUSTER[3]: 45.0},
        2: {PI_CLUSTER[1]: 120.0, PI_CLUSTER[3]: 85.5},
        3: {PI_CLUSTER[1]: 45.0,  PI_CLUSTER[2]: 85.5}
    }
    return matrix

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sim_step = 0
    
    print("Starting Laptop Orbital Simulation Orchestrator...")
    
    while True:
        print(f"\n--- Simulation Step {sim_step} ---")
        # 1. Compute where the satellites are right now
        raw_matrix = calculate_orbital_latencies(sim_step)
        
        # 2. Iterate through each Pi and push its custom directional routing map
        for pi_id, target_map in raw_matrix.items():
            pi_ip = PI_CLUSTER[pi_id]
            
            # Adjust values to strip out the physical hardware baseline latency
            adjusted_map = {}
            for target_ip, simulated_delay in target_map.items():
                adjusted_delay = max(0.0, simulated_delay - PHYSICAL_BASELINE_OVERHEAD)
                adjusted_map[target_ip] = round(adjusted_delay, 2)
            
            # Convert map to JSON string and blast it to that specific Pi's listener daemon
            json_payload = json.dumps(adjusted_map).encode('utf-8')
            sock.sendto(json_payload, (pi_ip, UDP_PORT))
            print(f"Sent updated latency matrix to Pi {pi_id} ({pi_ip})")
            
        # 3. Wait for the next orbital calculation interval (e.g., every 1 second)
        sim_step += 1
        time.sleep(1.0)

if __name__ == "__main__":
    main()