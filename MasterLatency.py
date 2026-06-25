import socket
import json
import time

# ==============================================================================
# EDIT THESE CONSTANT VARIABLES TO CHANGE LATENCIES ACROSS THE NETWORK
# ==============================================================================
MANUAL_LATENCY_CONFIG = {
    1: {
        "10.0.0.12": 180.0,  # Latency from Pi 1 to Pi 2 (in ms)
        "10.0.0.13": 35.0    # Latency from Pi 1 to Pi 3 (in ms)
    },
    2: {
        "10.0.0.11": 180.0,  # Latency from Pi 2 to Pi 1 (in ms)
    }
}

# Static IP map matching your physical Pi setup
PI_CLUSTER = {
    1: "10.0.0.11",
    2: "10.0.0.12",
    3: "10.0.0.13",
}

UDP_PORT = 5005
PHYSICAL_BASELINE_OVERHEAD = 0.5 

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("==================================================")
    print("      Laptop Live Latency Controller Active       ")
    print("==================================================\n")
    
    while True:
        for pi_id, target_map in MANUAL_LATENCY_CONFIG.items():
            if pi_id not in PI_CLUSTER: continue
            pi_ip = PI_CLUSTER[pi_id]
            
            adjusted_map = {}
            for target_ip, static_delay in target_map.items():
                adjusted_delay = max(0.0, static_delay - PHYSICAL_BASELINE_OVERHEAD)
                adjusted_map[target_ip] = round(adjusted_delay, 2)
            
            json_payload = json.dumps(adjusted_map).encode('utf-8')
            sock.sendto(json_payload, (pi_ip, UDP_PORT))
            
        print("Pushed latency map variables to the cluster. Sleeping for 2s...")
        time.sleep(2.0)

if __name__ == "__main__":
    main()