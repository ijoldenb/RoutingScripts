#!/usr/bin/env python3
import socket
import json
import time

TELEMETRY_PORT = 65001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", TELEMETRY_PORT))

print(f"==================================================")
print(f"[*] LATENCY COLLECTOR ONLINE (Port {TELEMETRY_PORT})")
print(f"==================================================")

pending_tcp = {}
pending_icmp = {}
last_cleanup = time.time()

while True:
    try:
        data, _ = sock.recvfrom(8192)
        msg = json.loads(data.decode('utf-8'))

        proto = msg.get("proto")
        pi_id = msg.get("pi")
        direction = msg.get("dir")
        src_ip = msg.get("src")
        dst_ip = msg.get("dst")
        ts = msg.get("ts")

        # 1. ICMP (PING)
        if proto == "icmp":
            seq = msg.get("seq")
            if direction == "tx" and msg.get("type") == "request":
                pending_icmp[(pi_id, dst_ip, seq)] = ts

            elif direction == "rx" and msg.get("type") == "reply":
                key = (pi_id, src_ip, seq)
                if key in pending_icmp:
                    tx_ts = pending_icmp.pop(key)
                    rtt_ms = (ts - tx_ts) * 1000.0
                    if rtt_ms >= 0:
                        print(f"[PING RTT] Pi #{pi_id} ({dst_ip}) -> {src_ip} | Latency: {rtt_ms:.3f} ms")

        # 2. TCP
        elif proto == "tcp":
            sport = msg.get("sport")
            dport = msg.get("dport")
            seq = msg.get("seq", 0)
            ack = msg.get("ack", 0)
            pkt_len = msg.get("len", 0)

            if direction == "tx" and pkt_len > 0:
                expected_ack = seq + pkt_len
                pending_tcp[(pi_id, dst_ip, sport, expected_ack)] = ts

            elif direction == "rx" and ack > 0:
                key = (pi_id, src_ip, dport, ack)
                if key in pending_tcp:
                    tx_ts = pending_tcp.pop(key)
                    rtt_ms = (ts - tx_ts) * 1000.0
                    if rtt_ms >= 0:
                        print(f"[TCP RTT]  Pi #{pi_id} ({dst_ip}) -> {src_ip} | Latency: {rtt_ms:.3f} ms")

        # Memory Cleanup
        now = time.time()
        if now - last_cleanup > 5.0:
            if len(pending_tcp) > 10000:
                pending_tcp.clear()
            if len(pending_icmp) > 1000:
                pending_icmp.clear()
            last_cleanup = now

    except Exception:
        continue