import socket
import json
import csv
import time
from collections import defaultdict

# --- CONFIGURATION ---
TELEMETRY_PORT = 65001
CSV_FILENAME = "network_latency_results.csv"

# Vaults for tracking network states
trace_buffer = defaultdict(dict)  # Pairs individual packet tx/rx via ip_id
latest_legs = {}                  # Stores the most recent directional one-way calculation

# Initialize the CSV file with explicit Sender and Receiver headers
with open(CSV_FILENAME, mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Timestamp', 'Sender', 'Receiver', 'Two_Way_Latency_ms'])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

print(f"[*] Central Trace Collector listening on UDP {TELEMETRY_PORT}...")
print(f"[*] Writing directional 2-way RTT data to '{CSV_FILENAME}'...")
print("=========================================================================")

# Keep the file open in append mode, flushing entries immediately
with open(CSV_FILENAME, mode='a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    
    while True:
        data, addr = sock.recvfrom(1024)
        
        try:
            msg = json.loads(data.decode('utf-8'))
            
            packet_key = (msg["ip_id"], msg["src"], msg["dst"])
            direction = msg["dir"]
            timestamp = msg["ts"]
            
            # Buffer the raw telemetry timestamps for this specific packet ID
            trace_buffer[packet_key][direction] = timestamp
            
            # 1. Once an individual physical packet leg completes (both tx and rx arrived)
            if "tx" in trace_buffer[packet_key] and "rx" in trace_buffer[packet_key]:
                tx_time = trace_buffer[packet_key]["tx"]
                rx_time = trace_buffer[packet_key]["rx"]
                
                # Compute raw one-way transit (warped by clock skew)
                one_way_ms = (rx_time - tx_time) * 1000.0
                
                src = msg["src"]
                dst = msg["dst"]
                
                # Save this leg's current calculation
                latest_legs[(src, dst)] = one_way_ms
                
                # 2. Check if the reverse round-trip leg has also finished
                if (dst, src) in latest_legs:
                    # Combining opposing legs mathematically deletes the clock skew
                    two_way_ms = latest_legs[(src, dst)] + latest_legs[(dst, src)]
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Because (dst, src) was already waiting in the vault, 
                    # 'dst' is the host that originally initiated this round trip.
                    sender = dst
                    receiver = src
                    
                    # Print result to console showing directional flow
                    print(f"[RTT] {sender} -> {receiver} | 2-Way Latency: {two_way_ms:.3f} ms")
                    
                    # Write immediately to CSV
                    writer.writerow([current_time, sender, receiver, f"{two_way_ms:.3f}"])
                    csv_file.flush() 
                    
                    # Clear paired legs out of memory cache
                    del latest_legs[(src, dst)]
                    del latest_legs[(dst, src)]
                    
                # Purge raw single packet state from tracking buffer
                del trace_buffer[packet_key]

        except json.JSONDecodeError:
            continue