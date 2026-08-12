import os
import sys
import time
import socket
import json
from scapy.all import sniff, IP, get_if_addr
import yaml

# --- CONFIGURATION ---
MAIN_PC_IP = "192.168.0.243"  # Main PC IP
TELEMETRY_PORT = 65001        # Port the Main PC listens on
TARGET_INTERFACE = "eth0"     # Physical interface on the Pi
CONFIG_PATH = os.path.expanduser("~/RoutingScripts/control_IP.yaml")

# Detect this Pi's IP address on eth0
try:
    MY_IP = get_if_addr(TARGET_INTERFACE)
except Exception as e:
    print(f"[FATAL] Unable to get IP for {TARGET_INTERFACE}: {e}")
    sys.exit(1)

# Function to load config and identify THIS Pi's ID
def get_my_pi_id(file_path, my_ip):
    if not os.path.exists(file_path):
        print(f"[WARNING] Config file not found at {file_path}. Defaulting ID to 'Unknown'.")
        return "Unknown"
        
    with open(file_path) as f:
        data = yaml.safe_load(f)
        
    if isinstance(next(iter(data.values())), dict):
        data = next(iter(data.values()))
        
    # Match MY_IP against the config to find our Pi ID
    for pi_id, ip in data.items():
        if str(ip).strip() == my_ip:
            # Extract numeric ID if key is formatted like "pi1" or "Node_1"
            return str(pi_id)
            
    return "Unknown"

PI_ID = get_my_pi_id(CONFIG_PATH, MY_IP)

# BPF FILTER: Capture IP traffic, ignoring telemetry and time-sync traffic
BPF_FILTER = f"ip and not port {TELEMETRY_PORT} and not port 319 and not port 320 and not port 123"

telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def process_packet(pkt):
    if IP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        pkt_id = int(pkt[IP].id)
        
        # FIX: Cast Scapy EDecimal to standard Python float for JSON
        timestamp = float(pkt.time) 
        
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
            # print(f"[DEBUG] Sent telemetry for pkt {pkt_id} ({direction})")
        except Exception as e:
            print(f"[ERROR] Telemetry send failed: {e}")

print(f"[*] Pi #{PI_ID} Tracer Active ({MY_IP}). Sniffing on {TARGET_INTERFACE}...")
sniff(iface=TARGET_INTERFACE, filter=BPF_FILTER, prn=process_packet, store=False)