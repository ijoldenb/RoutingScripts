import socket
import json
import time

# ==============================================================================
# MANUAL TEST CONFIGURATION
# Modify these values manually to test different static satellite links.
# Syntax: SOURCE_PI_ID: { TARGET_PI_IP: DESIRED_LATENCY_IN_MS }
# ==============================================================================
MANUAL_LATENCY_CONFIG = {
    1: {
        "192.168.0.198": 120.0,  # Pi 1 to Pi 2 latency
    },
    2: {
        "192.168.0.244": 100.0,  # Pi 2 to Pi 1 latency
    },
}

# Mapping of Pi IDs to their actual control IP addresses on your testbed
PI_CLUSTER = {
    1: "192.168.0.198",
    2: "192.168.0.244",
    # Add more Pis here as needed (up to 20)
}

UDP_PORT = 5005
PHYSICAL_BASELINE_OVERHEAD = 0.5  # Subtracted to compensate for Aruba 2920 & cables

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("==================================================")
    print("               Manual Latency Running             ")
    print("==================================================")
    print("Press Ctrl+C to stop. Edit the script to change values.\n")
    
    while True:
        # Process each Pi defined in your manual configuration block
        for pi_id, target_map in MANUAL_LATENCY_CONFIG.items():
            if pi_id not in PI_CLUSTER:
                print(f"Warning: Pi ID {pi_id} is missing an IP mapping in PI_CLUSTER.")
                continue
                
            pi_ip = PI_CLUSTER[pi_id]
            adjusted_map = {}
            
            # Calculate and adjust the latency values
            for target_ip, static_delay in target_map.items():
                adjusted_delay = max(0.0, static_delay - PHYSICAL_BASELINE_OVERHEAD)
                adjusted_map[target_ip] = round(adjusted_delay, 2)
            
            # Serialize payload and stream it out
            json_payload = json.dumps(adjusted_map).encode('utf-8')
            try:
                sock.sendto(json_payload, (pi_ip, UDP_PORT))
                print(f"Pushed static configuration to Pi {pi_id} ({pi_ip}) -> {adjusted_map}")
            except Exception as e:
                print(f"Failed sending to Pi {pi_id}: {e}")
                
        print("--------------------------------------------------")
        time.sleep(2.0)  # Refresh baseline rules every 2 seconds

if __name__ == "__main__":
    main()