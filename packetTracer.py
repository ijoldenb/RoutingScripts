#!/usr/bin/env python3
import os
import sys
import time
import socket
import json
import zlib  # Fast built-in CRC hashing for UDP packet fingerprints
import yaml
from scapy.all import sniff, IP, TCP, UDP, ICMP, get_if_addr

# --- CONFIGURATION ---
MAIN_PC_IP = "192.168.0.243"  # Central Laptop / Collector IP
TELEMETRY_PORT = 65001        # Port telemCollector.py listens on
TARGET_INTERFACE = "eth0"     # Physical interface on the Pi
CONFIG_PATH = os.path.expanduser("~/RoutingScripts/control_IP.yaml")

# Detect this Pi's IP address on eth0
try:
    MY_IP = get_if_addr(TARGET_INTERFACE)
except Exception as e:
    print(f"[FATAL] Unable to get IP address for interface {TARGET_INTERFACE}: {e}")
    sys.exit(1)

# Function to load config and identify THIS Pi's ID
def get_my_pi_id(file_path, my_ip):
    if not os.path.exists(file_path):
        print(f"[WARNING] Config file not found at {file_path}. Defaulting ID to 'Unknown'.")
        return "Unknown"
        
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
            
        if isinstance(next(iter(data.values())), dict):
            data = next(iter(data.values()))
            
        # Match MY_IP against the config to find our Pi ID
        for pi_id, ip in data.items():
            if str(ip).strip() == my_ip:
                return str(pi_id)
    except Exception as e:
        print(f"[WARNING] Failed to parse {file_path}: {e}")
        
    return "Unknown"

PI_ID = get_my_pi_id(CONFIG_PATH, MY_IP)

# BPF FILTER: Capture IP traffic, explicitly ignoring:
# - Telemetry traffic (65001)
# - PTP Clock Sync traffic (319, 320)
# - NTP / Chrony Clock Sync traffic (123)
BPF_FILTER = f"ip and not port {TELEMETRY_PORT} and not port 319 and not port 320 and not port 123"

telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def process_packet(pkt):
    # Quick filter: ignore packets not involving local IP to reduce JSON load
    if IP not in pkt:
        return
        
    src_ip = pkt[IP].src
    dst_ip = pkt[IP].dst
    
    # Grab kernel capture timestamp directly
    timestamp = float(pkt.time)

    # Use IP Header ID instead of hashing raw payloads for UDP during high throughput
    if TCP in pkt:
        pkt_id = f"tcp_{pkt[TCP].seq}"
    elif UDP in pkt:
        pkt_id = f"udp_{pkt[UDP].sport}_{pkt[UDP].dport}_{pkt[IP].id}"
    else:
        pkt_id = f"ip_{pkt[IP].id}"

    direction = "tx" if src_ip == MY_IP else "rx"

    telemetry_data = {
        "pi": PI_ID,
        "dir": direction,
        "ip_id": pkt_id,
        "src": src_ip,
        "dst": dst_ip,
        "ts": timestamp
    }

    try:
        payload = json.dumps(telemetry_data).encode('utf-8')
        telemetry_sock.sendto(payload, (MAIN_PC_IP, TELEMETRY_PORT))
    except Exception:
        pass  # Avoid printing errors in hot loop to prevent stdout blocking

# --- START SNIFFER ---
print(f"[*] Pi #{PI_ID} Packet Tracer Active ({MY_IP}). Sniffing on {TARGET_INTERFACE}...")
sniff(iface=TARGET_INTERFACE, filter=BPF_FILTER, prn=process_packet, store=False)