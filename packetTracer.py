import time
import socket
import json
from scapy.all import sniff, IP, get_if_addr

# --- CONFIGURATION ---
PI_ID = 1                     # Change this for Pi 2, Pi 3, Pi 4
MAIN_PC_IP = "192.168.0.243"  # Main PC IP on the 192.168.0.x network
TELEMETRY_PORT = 65001        # Port the Main PC listens on
TARGET_INTERFACE = "eth0"     # Physical interface on the Pi

# Automatically detect this Pi's IP address on eth0 to determine tx/rx
MY_IP = get_if_addr(TARGET_INTERFACE)

# BPF FILTER: Capture IP traffic, but explicitly IGNORE:
# - Telemetry traffic (65001)
# - PTP Clock Sync traffic (319, 320)
# - NTP / Chrony Clock Sync traffic (123)
BPF_FILTER = f"ip and not port {TELEMETRY_PORT} and not port 319 and not port 320 and not port 123"

telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def process_packet(pkt):
    if IP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        pkt_id = pkt[IP].id  
        timestamp = pkt.time 
        
        # If the source IP matches this Pi, it's an outbound transmission (tx)
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
            pass

print(f"[*] Pi {PI_ID} Tracer Active ({MY_IP}). Sniffing on {TARGET_INTERFACE}...")
sniff(iface=TARGET_INTERFACE, filter=BPF_FILTER, prn=process_packet, store=False)