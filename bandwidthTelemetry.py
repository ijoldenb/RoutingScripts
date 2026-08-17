import socket
import json
import time
from collections import defaultdict

TELEMETRY_PORT = 65002
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

# Track byte counts per flow: (src_ip, dst_ip) -> total_bytes
flow_bytes = defaultdict(int)
last_flush = time.time()

print(f"[*] Flow Bandwidth Collector Active on UDP {TELEMETRY_PORT}...")
print("=========================================================================")

while True:
    try:
        data, _ = sock.recvfrom(2048)
        msg = json.loads(data.decode('utf-8'))
        
        # Only aggregate RX (received) packets at the endpoint to reflect true throughput
        if msg.get("dir") == "rx":
            flow_key = (msg["src"], msg["dst"])
            flow_bytes[flow_key] += msg.get("len", 0)

        # Every 1 second, calculate and display flow throughput
        now = time.time()
        if now - last_flush >= 1.0:
            elapsed = now - last_flush
            timestamp = time.strftime("%H:%M:%S")
            
            if flow_bytes:
                print(f"\n--- Data Throughput Summary ({timestamp}) ---")
                for (src, dst), total_bytes in flow_bytes.items():
                    mbps = (total_bytes * 8) / (elapsed * 1_000_000)
                    print(f" {src} -> {dst} | Bandwidth: {mbps:6.2f} Mbps")
                flow_bytes.clear()
            
            last_flush = now

    except Exception:
        continue