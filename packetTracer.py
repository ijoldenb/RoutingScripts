#!/usr/bin/env python3
import os
import sys
import socket
import json
import yaml
import subprocess
import zlib
from scapy.all import get_if_addr, get_if_addrs

# --- CONFIGURATION ---
MAIN_PC_IP = "192.168.0.243"      # Central Collector IP
TELEMETRY_PORTS = [65001, 65002]  # 65001: RTT | 65002: Bandwidth
AGENT_PORT = 65000                # Port tc agent listens on
TARGET_INTERFACE = "eth0"         # Dedicated simulation network interface
CONFIG_PATH = os.path.expanduser("~/RoutingScripts/control_IP.yaml")

# Collect all local IPs to identify outgoing (tx) packets
try:
    MY_IPS = set(get_if_addrs())
    ETH0_IP = get_if_addr(TARGET_INTERFACE)
except Exception as e:
    print(f"[FATAL] Unable to detect IP addresses for {TARGET_INTERFACE}: {e}")
    sys.exit(1)

def get_my_pi_id(file_path, my_ips):
    if not os.path.exists(file_path):
        return "Unknown"
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
        if isinstance(next(iter(data.values())), dict):
            data = next(iter(data.values()))
        for pi_id, ip in data.items():
            if str(ip).strip() in my_ips:
                return str(pi_id)
    except Exception:
        pass
    return "Unknown"

PI_ID = get_my_pi_id(CONFIG_PATH, MY_IPS)

# UDP telemetry socket with enlarged kernel buffer to handle traffic bursts
telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 * 1024 * 1024)

# BPF filter excluding control and telemetry ports from capture
ports_filter = " and ".join([f"not port {p}" for p in TELEMETRY_PORTS]) + f" and not port {AGENT_PORT}"
tcpdump_cmd = [
    "sudo", "tcpdump", "-i", TARGET_INTERFACE, "-B", "4096", "-tt", "-n", "-l",
    f"(tcp or udp or icmp) and {ports_filter}"
]

print(f"[*] Pi #{PI_ID} Tracer Active on {TARGET_INTERFACE} ({ETH0_IP}). Sniffing simulation traffic...")
print(f"[*] Dual-streaming telemetry to {TELEMETRY_PORTS}...")

proc = subprocess.Popen(
    tcpdump_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    bufsize=8192
)

def parse_line(line):
    parts = line.strip().split()
    
    # Ignore incomplete or non-IP frames
    if "IP" not in parts or ">" not in parts:
        return None

    try:
        ts = float(parts[0])
        gt_idx = parts.index(">")

        # Dynamically locate source and destination relative to the direction arrow '>'
        src_full = parts[gt_idx - 1]
        dst_full = parts[gt_idx + 1].rstrip(':')

        # 1. ICMP Traffic
        if "ICMP" in line:
            src_ip = src_full
            dst_ip = dst_full
            icmp_type = "request" if "echo request" in line else ("reply" if "echo reply" in line else None)
            if not icmp_type:
                return None
            
            seq = 0
            if "seq " in line:
                seq = int(line.split("seq ")[1].split(",")[0].split()[0])

            direction = "tx" if src_ip in MY_IPS else "rx"
            return {
                "proto": "icmp",
                "pi": PI_ID,
                "dir": direction,
                "ip_id": f"icmp_{seq}",
                "src": src_ip,
                "dst": dst_ip,
                "type": icmp_type,
                "seq": seq,
                "ts": ts,
                "len": 64
            }

        # 2. TCP & UDP Traffic
        src_ip, sport_str = src_full.rsplit('.', 1)
        dst_ip, dport_str = dst_full.rsplit('.', 1)
        sport, dport = int(sport_str), int(dport_str)

        proto = "udp" if "UDP" in line else "tcp"
        pkt_len = 0

        if "length " in line:
            pkt_len = int(line.split("length ")[1].split()[0].rstrip(':'))

        seq = 0
        ack = 0

        if proto == "tcp":
            if "seq " in line:
                seq_str = line.split("seq ")[1].split(",")[0].split()[0]
                seq = int(seq_str.split(":")[0]) if ":" in seq_str else int(seq_str)
            if "ack " in line:
                ack = int(line.split("ack ")[1].split(",")[0].split()[0])
            pkt_id = f"tcp_{seq}"
        else:
            # Unique UDP fingerprint based on ports, payload length, and CRC32
            pkt_id = f"udp_{sport}_{dport}_{pkt_len}_{zlib.crc32(line.encode('utf-8'))}"

        direction = "tx" if src_ip in MY_IPS else "rx"
        return {
            "proto": proto,
            "pi": PI_ID,
            "dir": direction,
            "ip_id": pkt_id,
            "src": src_ip,
            "dst": dst_ip,
            "sport": sport,
            "dport": dport,
            "seq": seq,
            "ack": ack,
            "len": pkt_len,
            "ts": ts
        }

    except Exception:
        return None

try:
    for line in iter(proc.stdout.readline, ''):
        telemetry_data = parse_line(line)
        if telemetry_data:
            payload = json.dumps(telemetry_data).encode('utf-8')
            for port in TELEMETRY_PORTS:
                try:
                    telemetry_sock.sendto(payload, (MAIN_PC_IP, port))
                except socket.error:
                    pass

except KeyboardInterrupt:
    proc.terminate()
    sys.exit(0)