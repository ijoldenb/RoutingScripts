#!/usr/bin/env python3
import socket
import json
import time

TELEMETRY_PORT = 65002
REPORT_INTERVAL = 1.0  # Output throughput summary every 1 second

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

print(f"==================================================")
print(f"[*] BANDWIDTH COLLECTOR ONLINE (Port {TELEMETRY_PORT})")
print(f"==================================================")

# Store total accumulated bytes per flow: (pi_id, src_ip, dst_ip) -> byte_count
bw_counter = {}
last_bw_report = time.time()

while True:
    try:
        data, _ = sock.recvfrom(8192)
        msg = json.loads(data.decode('utf-8'))

        direction = msg.get("dir")
        pi_id = msg.get("pi")
        src_ip = msg.get("src")
        dst_ip = msg.get("dst")
        pkt_len = msg.get("len", 0)

        # Accumulate transmitted payload bytes
        if direction == "tx" and pkt_len > 0:
            flow_key = (pi_id, src_ip, dst_ip)
            bw_counter[flow_key] = bw_counter.get(flow_key, 0) + pkt_len

        # Output Rate Summary Every Interval
        now = time.time()
        bw_elapsed = now - last_bw_report

        if bw_elapsed >= REPORT_INTERVAL:
            if bw_counter:
                print(f"--- Traffic Summary ({time.strftime('%H:%M:%S')}) ---")
                for (pi, src, dst), total_bytes in list(bw_counter.items()):
                    mbps = (total_bytes * 8) / (bw_elapsed * 1_000_000)
                    if mbps >= 0.01:
                        print(f"  Pi #{pi} | {src} -> {dst} | Rate: {mbps:6.2f} Mbps | Total: {total_bytes:,} bytes")
                print()

            bw_counter.clear()
            last_bw_report = now

    except Exception:
        continue