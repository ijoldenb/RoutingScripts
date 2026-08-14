#!/usr/bin/env python3
import socket
import json
import time

TELEMETRY_PORT = 65002
REPORT_INTERVAL = 1.0  # Report bandwidth every 1 second

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", TELEMETRY_PORT))
sock.settimeout(1.0)  # Non-blocking check every 1 second

print("==================================================")
print(f"[*] DATA BANDWIDTH COLLECTOR ONLINE (Port {TELEMETRY_PORT})")
print("==================================================")

bw_counter = {}
last_bw_report = time.time()
total_pkts_seen = 0

while True:
    try:
        data, _ = sock.recvfrom(8192)
        msg = json.loads(data.decode('utf-8'))
        total_pkts_seen += 1

        direction = msg.get("dir", "tx")
        pi_id = msg.get("pi", "?")
        src_ip = msg.get("src", "?")
        dst_ip = msg.get("dst", "?")
        pkt_len = msg.get("len", 0)

        # STRICT FILTER: Ignore empty TCP ACKs and zero-length control frames
        if pkt_len > 0:
            flow_key = (pi_id, direction, src_ip, dst_ip)
            bw_counter[flow_key] = bw_counter.get(flow_key, 0) + pkt_len

    except socket.timeout:
        pass
    except Exception:
        continue

    # Periodic calculation
    now = time.time()
    bw_elapsed = now - last_bw_report

    if bw_elapsed >= REPORT_INTERVAL:
        timestamp = time.strftime('%H:%M:%S')
        if bw_counter:
            print(f"--- Data Throughput Summary ({timestamp}) ---")
            for (pi, dir_type, src, dst), total_bytes in list(bw_counter.items()):
                mbps = (total_bytes * 8) / (bw_elapsed * 1_000_000)
                if mbps >= 0.01:  # Filter out tiny residual noise
                    dir_label = "TX (Out)" if dir_type == "tx" else "RX (In) "
                    print(f"  Pi #{pi} | [{dir_label}] {src} -> {dst} | Data Rate: {mbps:6.2f} Mbps")
            print()
        else:
            print(f"[{timestamp}] Listening on port {TELEMETRY_PORT}... Total Telemetry Rx: {total_pkts_seen}")

        bw_counter.clear()
        last_bw_report = now