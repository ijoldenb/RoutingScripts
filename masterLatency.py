import socket
import json
import time
import sys

# ==============================================================================
# --- NETWORK IDENTIFICATION MAPPINGS ---
# ==============================================================================
# The external SSH IP addresses to reach each Pi
PI_CLUSTER = {
    1: "192.168.0.244",
    2: "192.168.0.198",
    3: "192.168.0.129",
    4: "192.168.0.237",
}

# The internal VPN/VLAN IPs that `tc` runs against. 
# Pi 1 needs to know target IP "192.168.102.10" to delay traffic to Pi 2.
TARGET_IPS = {
    1: "192.168.101.10",
    2: "192.168.102.10",
    3: "192.168.103.10",
    4: "192.168.104.10",
}

UDP_PORT = 65000
PHYSICAL_BASELINE_OVERHEAD = 4

def parse_yaml_trace(file_path):
    timelineMap = {}
    scheduleTime = 0.0
    inLink = False
    tempChange = {}

    try:
        with open(file_path, "r") as traceFile:
            for line in traceFile:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                
                key, valStr = [x.strip() for x in line.split(":", 1)]

                if "- time" in key:
                    scheduleTime = float(valStr)
                elif "- src" in key:
                    tempChange['src'] = int(valStr)
                    inLink = True
                elif inLink and "dst" in key:
                    tempChange['dst'] = int(valStr)
                elif inLink and "latency" in key:
                    # In our generator, latency is the last element of the block.
                    # We save the block to the timeline map here.
                    tempChange['latency'] = float(valStr)
                    
                    if scheduleTime not in timelineMap:
                        timelineMap[scheduleTime] = []
                    timelineMap[scheduleTime].append(tempChange.copy())
                    
                    inLink = False
                    tempChange = {}
    except FileNotFoundError:
        print(f"FATAL ERROR: Missing trajectory map at {file_path}!")
        sys.exit(1)
        
    return timelineMap

def main():
    trace_file = "/home/ijoldenb/ns-3.48/scratch/topology_trace.yaml"
    print("Parsing topology trace for Latency schedules...")
    timeline = parse_yaml_trace(trace_file)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("==================================================")
    print("      YAML Live Latency Controller Active         ")
    print("==================================================\n")
    
    start_time = time.time()
    
    for sim_time in sorted(timeline.keys()):
        # Calculate how long to wait until this simulation timestamp occurs
        time_to_wait = sim_time - (time.time() - start_time)
        if time_to_wait > 0:
            time.sleep(time_to_wait)
            
        print(f"[{sim_time}s] Applying latency updates...")
        
        # Build node-specific configurations for this timeframe
        # Structure: { pi_id: { "target_ip": latency, ... } }
        current_config = {i: {} for i in PI_CLUSTER.keys()}
        
        for link in timeline[sim_time]:
            src = link['src']
            dst = link['dst']
            latency = link['latency']
            
            adjusted_latency = max(0.0, latency - PHYSICAL_BASELINE_OVERHEAD)
            
            # Since the graph is symmetric, we populate both directions
            if src in PI_CLUSTER and dst in TARGET_IPS:
                current_config[src][TARGET_IPS[dst]] = round(adjusted_latency, 2)
            if dst in PI_CLUSTER and src in TARGET_IPS:
                current_config[dst][TARGET_IPS[src]] = round(adjusted_latency, 2)
                
        # Dispatch the JSON configs via UDP to each Pi
        for pi_id, target_map in current_config.items():
            if not target_map:
                continue
                
            pi_ip = PI_CLUSTER[pi_id]
            try:
                json_payload = json.dumps(target_map).encode('utf-8')
                sock.sendto(json_payload, (pi_ip, UDP_PORT))
            except Exception as e:
                print(f"  -> Failed to send to Pi {pi_id}: {e}")

if __name__ == "__main__":
    main()