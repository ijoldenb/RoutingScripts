import socket
import json
from collections import defaultdict

# --- CONFIGURATION ---
TELEMETRY_PORT = 65001

# Advanced tracking vault: trace_buffer[(ip_id, src, dst)] = {"tx": time, "rx": time}
trace_buffer = defaultdict(dict)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

print(f"[*] Central Trace Collector listening on UDP {TELEMETRY_PORT}...")
print("=========================================================================")

while True:
    data, addr = sock.recvfrom(1024)
    
    try:
        msg = json.loads(data.decode('utf-8'))
        
        # Create a unique structural key for this exact packet flow
        packet_key = (msg["ip_id"], msg["src"], msg["dst"])
        direction = msg["dir"]
        timestamp = msg["ts"]
        
        # Store the timestamp
        trace_buffer[packet_key][direction] = timestamp
        
        # Once we have captured both the physical departure and arrival
        if "tx" in trace_buffer[packet_key] and "rx" in trace_buffer[packet_key]:
            tx_time = trace_buffer[packet_key]["tx"]
            rx_time = trace_buffer[packet_key]["rx"]
            
            latency_ms = (rx_time - tx_time) * 1000.0
            
            print(f"[ID: {msg['ip_id']:<5}] {msg['src']} -> {msg['dst']} | Physical Latency: {latency_ms:.3f} ms")
            
            # Clean up tracking history to preserve memory
            del trace_buffer[packet_key]

    except json.JSONDecodeError:
        continue