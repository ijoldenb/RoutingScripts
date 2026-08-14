#!/usr/bin/env python3
import socket
import json
import time

TELEMETRY_PORT = 65002
REPORT_INTERVAL = 1.0  # Calculate bandwidth every 1 second

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

print("==================================================")
print(f"[*] BANDWIDTH COLLECTOR ONLINE (Port {TELEMETRY_PORT})")
print("==================================================")

# Dictionary key: (pi_id, direction, src_ip, dst_ip) -> total_bytes
bw_counter = {}
last_bw_report = time.time()
pkt_received_flag = False

while True:
    try:
        data, _ = sock.recvfrom(8192)
        msg = json.loads(data.decode('utf-8'))
        pkt_received_flag = True

        direction = msg.get("dir", "tx")
        pi_id = msg.get("pi", "?")
        src_ip = msg.get("src", "?")
        dst_ip = msg.get("dst", "?")
        pkt_len = msg.get("len", 0)

        # If length was 0 (e.g. pure TCP ACKs or raw frames), estimate 66 bytes for L2/L3/L4 headers
        effective_bytes = pkt_len if pkt_len > 0 else 66

        flow_key = (pi_id, direction, src_ip, dst_ip)
        bw_counter[flow_key] = bw_counter.get(flow_key, 0) + effective_bytes

        # Output Rate Summary Every Interval
        now = time.time()
        bw_elapsed = now - last_bw_report

        if bw_elapsed >= REPORT_INTERVAL:
            if bw_counter:
                timestamp = time.strftime('%H:%M:%S')
                print(f"--- Bandwidth Summary ({timestamp}) ---")
                for (pi, dir_type, src, dst), total_bytes in list(bw_counter.items()):
                    mbps = (total_bytes * 8) / (bw_elapsed * 1_000_000)
                    dir_label = "TX (Out)" if dir_type == "tx" else "RX (In) "
                    print(f"  Pi #{pi} | [{dir_label}] {src} -> {dst} | Rate: {mbps:6.2f} Mbps | Bytes: {total_bytes:,}")
                print()
            elif not pkt_received_flag:
                print("[IDLE] Waiting for telemetry stream from Pi tracer...")

            bw_counter.clear()
            last_bw_report = now

    except Exception:
        continue