#!/usr/bin/env python3
import os
import sys
import socket
import json
import yaml
import subprocess
import re
from scapy.all import get_if_addr

# --- CONFIGURATION ---
MAIN_PC_IP = "192.168.0.243"  # Central Laptop / Collector IP
TELEMETRY_PORT = 65001        # Port telemCollector.py listens on
AGENT_PORT = 65000            # Port tc agent listens on
TARGET_INTERFACE = "eth0"     # Physical interface on the Pi
CONFIG_PATH = os.path.expanduser("~/RoutingScripts/control_IP.yaml")

# Detect this Pi's IP address on eth0
try:
    MY_IP = get_if_addr(TARGET_INTERFACE)
except Exception as e:
    print(f"[FATAL] Unable to get IP address for interface {TARGET_INTERFACE}: {e}")
    sys.exit(1)

def get_my_pi_id(file_path, my_ip):
    if not os.path.exists(file_path):
        return "Unknown"
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
        if isinstance(next(iter(data.values())), dict):
            data = next(iter(data.values()))
        for pi_id, ip in data.items():
            if str(ip).strip() == my_ip:
                return str(pi_id)
    except Exception:
        pass
    return "Unknown"

PI_ID = get_my_pi_id(CONFIG_PATH, MY_IP)

# Create non-blocking UDP socket to prevent buffer locking
telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry_sock.setblocking(False)

# Pre-compile regex matchers for robust line parsing
ip_port_re = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+)\s+>\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+)')
seq_re = re.compile(r'seq (\d+)')
ack_re = re.compile(r'ack (\d+)')
len_re = re.compile(r'length (\d+)')

tcpdump_cmd = [
    "sudo", "tcpdump", "-i", TARGET_INTERFACE, "-tt", "-n", "-l",
    f"tcp and not port {TELEMETRY_PORT} and not port {AGENT_PORT}"
]

print(f"[*] Pi #{PI_ID} Tracer Active ({MY_IP}). Sniffing {TARGET_INTERFACE}...")

proc = subprocess.Popen(
    tcpdump_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    bufsize=1024
)

# Counter for packet sampling during heavy load
pkt_count = 0

try:
    for line in iter(proc.stdout.readline, ''):
        pkt_count += 1
        
        # Global exception handler prevents ANY single line from crashing the process
        try:
            parts = line.strip().split()
            if len(parts) < 5 or parts[1] != "IP":
                continue

            # 1. Microsecond Kernel Timestamp
            timestamp = float(parts[0])

            # 2. Extract IPs and Ports safely via Regex
            match = ip_port_re.search(line)
            if not match:
                continue

            src_ip, sport, dst_ip, dport = match.groups()

            # 3. Extract TCP Fields
            seq_match = seq_re.search(line)
            ack_match = ack_re.search(line)
            len_match = len_re.search(line)

            seq_num = int(seq_match.group(1)) if seq_match else 0
            ack_num = int(ack_match.group(1)) if ack_match else 0
            pkt_len = int(len_match.group(1)) if len_match else 0

            # 4. Optional Sampling: Skip pure zero-len data acknowledgments under high load
            # Keeps telemetry lightweight during multigigabyte file streams
            if pkt_len == 0 and ack_num == 0 and pkt_count % 2 != 0:
                continue

            direction = "tx" if src_ip == MY_IP else "rx"

            telemetry_data = {
                "pi": PI_ID,
                "dir": direction,
                "src": src_ip,
                "dst": dst_ip,
                "sport": int(sport),
                "dport": int(dport),
                "seq": seq_num,
                "ack": ack_num,
                "len": pkt_len,
                "ts": timestamp
            }

            payload = json.dumps(telemetry_data).encode('utf-8')
            
            # Send telemetry safely (drop packet if socket buffer is temporarily full)
            try:
                telemetry_sock.sendto(payload, (MAIN_PC_IP, TELEMETRY_PORT))
            except (OSError, socket.error):
                pass  # Ignore temporary buffer overflows

        except Exception:
            continue  # Catch parsing errors on non-standard packets and keep running

except KeyboardInterrupt:
    proc.terminate()
    sys.exit(0)