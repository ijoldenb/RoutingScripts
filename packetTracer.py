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
    if IP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        # Cast Scapy's high-precision EDecimal timestamp to a standard Python float for JSON
        timestamp = float(pkt.time)
        
        # --- PROTOCOL-SPECIFIC UNIQUE KEYING ---
        if TCP in pkt:
            # TCP uses Sequence Number
            pkt_id = f"tcp_{pkt[TCP].seq}"
        elif ICMP in pkt:
            # ICMP uses Sequence ID
            pkt_id = f"icmp_{pkt[ICMP].seq}"
        elif UDP in pkt:
            # UDP fingerprint: Source Port + Dest Port + IP ID + CRC32 of Payload
            payload_bytes = bytes(pkt[UDP].payload)[:64]
            crc = zlib.crc32(payload_bytes)
            pkt_id = f"udp_{pkt[UDP].sport}_{pkt[UDP].dport}_{pkt[IP].id}_{crc}"
        else:
            # Fallback for standard IP traffic
            pkt_id = f"ip_{pkt[IP].id}"

        # Determine if this Pi transmitted or received this packet
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
        except Exception as e:
            print(f"[ERROR] Failed to send telemetry: {e}")

# --- START SNIFFER ---
print(f"[*] Pi #{PI_ID} Packet Tracer Active ({MY_IP}). Sniffing on {TARGET_INTERFACE}...")
sniff(iface=TARGET_INTERFACE, filter=BPF_FILTER, prn=process_packet, store=False)