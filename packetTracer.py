#!/usr/bin/env python3
import os
import sys
import socket
import json
import yaml
from scapy.all import sniff, IP, TCP, get_if_addr

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
            
        for pi_id, ip in data.items():
            if str(ip).strip() == my_ip:
                return str(pi_id)
    except Exception as e:
        print(f"[WARNING] Failed to parse {file_path}: {e}")
        
    return "Unknown"

PI_ID = get_my_pi_id(CONFIG_PATH, MY_IP)

# BPF FILTER: Strictly capture TCP traffic, ignoring telemetry port
BPF_FILTER = f"tcp and not port {TELEMETRY_PORT}"

telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def process_packet(pkt):
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        # High-precision packet arrival timestamp
        timestamp = float(pkt.time)
        
        # Extract TCP sequence, ack numbers, and payload length
        seq_num = pkt[TCP].seq
        ack_num = pkt[TCP].ack
        payload_len = len(pkt[TCP].payload)
        
        direction = "tx" if src_ip == MY_IP else "rx"

        # Structural payload tailored for TCP 2-Way RTT calculation
        telemetry_data = {
            "pi": PI_ID,
            "dir": direction,
            "src": src_ip,
            "dst": dst_ip,
            "sport": pkt[TCP].sport,
            "dport": pkt[TCP].dport,
            "seq": seq_num,
            "ack": ack_num,
            "len": payload_len,
            "flags": str(pkt[TCP].flags),
            "ts": timestamp
        }

        try:
            payload = json.dumps(telemetry_data).encode('utf-8')
            telemetry_sock.sendto(payload, (MAIN_PC_IP, TELEMETRY_PORT))
        except Exception:
            pass  # Suppress print statements in hot loop to preserve CPU

# --- START SNIFFER ---
print(f"[*] Pi #{PI_ID} Packet Tracer Active ({MY_IP}). Sniffing TCP on {TARGET_INTERFACE}...")
sniff(iface=TARGET_INTERFACE, filter=BPF_FILTER, prn=process_packet, store=False)