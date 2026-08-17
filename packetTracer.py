#!/usr/bin/env python3
import os
import sys
import socket
import json
import yaml
import subprocess
from scapy.all import get_if_addr

# --- CONFIGURATION ---
MAIN_PC_IP = "192.168.0.243"      # Central Collector IP
TELEMETRY_PORTS = [65001, 65002]  # 65001: RTT | 65002: Bandwidth
AGENT_PORT = 65000                # Port tc agent listens on
TARGET_INTERFACE = "eth0"         # Physical interface on the Pi
CONFIG_PATH = os.path.expanduser("~/RoutingScripts/control_IP.yaml")

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

telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry_sock.setblocking(False)

# Exclude all control and telemetry ports from capture
ports_filter = " and ".join([f"not port {p}" for p in TELEMETRY_PORTS]) + f" and not port {AGENT_PORT}"
tcpdump_cmd = [
    "sudo", "tcpdump", "-i", TARGET_INTERFACE, "-B", "8192", "-tt", "-n", "-l",
    f"(tcp or udp or icmp) and {ports_filter}"
]

print(f"[*] Pi #{PI_ID} Tracer Active ({MY_IP}). Dual-streaming telemetry to ports {TELEMETRY_PORTS}...")

proc = subprocess.Popen(
    tcpdump_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    bufsize=8192
)

def parse_line(line):
    parts = line.strip().split()
    if len(parts) < 4 or parts[1] != "IP":
        return None

    ts = float(parts[0])

    # 1. ICMP (PING)
    if "ICMP" in line:
        src_ip = parts[2]
        dst_ip = parts[4].rstrip(':')
        icmp_type = "request" if "echo request" in line else ("reply" if "echo reply" in line else None)
        if not icmp_type:
            return None
        
        seq = 0
        if "seq " in line:
            try:
                seq = int(line.split("seq ")[1].split(",")[0].split()[0])
            except Exception:
                pass

        direction = "tx" if src_ip == MY_IP else "rx"
        return {
            "proto": "icmp",
            "pi": PI_ID,
            "dir": direction,
            "src": src_ip,
            "dst": dst_ip,
            "type": icmp_type,
            "seq": seq,
            "ts": ts,
            "len": 64
        }

    # 2. TCP & UDP
    if ">" in parts:
        try:
            idx = parts.index(">")
            src_full = parts[idx - 1]
            dst_full = parts[idx + 1].rstrip(':')

            src_ip, sport = src_full.rsplit('.', 1)
            dst_ip, dport = dst_full.rsplit('.', 1)

            proto = "udp" if "UDP" in line else "tcp"
            pkt_len = 0

            if "length " in line:
                try:
                    pkt_len = int(line.split("length ")[1].split()[0].rstrip(':'))
                except Exception:
                    pkt_len = 0

            seq = 0
            ack = 0

            if proto == "tcp":
                if "seq " in line:
                    seq_str = line.split("seq ")[1].split(",")[0].split()[0]
                    seq = int(seq_str.split(":")[0]) if ":" in seq_str else int(seq_str)

                if "ack " in line:
                    ack = int(line.split("ack ")[1].split(",")[0].split()[0])

            direction = "tx" if src_ip == MY_IP else "rx"
            return {
                "proto": proto,
                "pi": PI_ID,
                "dir": direction,
                "src": src_ip,
                "dst": dst_ip,
                "sport": int(sport),
                "dport": int(dport),
                "seq": seq,
                "ack": ack,
                "len": pkt_len,
                "ts": ts
            }
        except Exception:
            return None

    return None

try:
    for line in iter(proc.stdout.readline, ''):
        try:
            telemetry_data = parse_line(line)
            if telemetry_data:
                payload = json.dumps(telemetry_data).encode('utf-8')
                # Dispatch payload to both RTT and Bandwidth collector ports
                for port in TELEMETRY_PORTS:
                    telemetry_sock.sendto(payload, (MAIN_PC_IP, port))
        except (OSError, socket.error):
            pass
        except Exception:
            continue

except KeyboardInterrupt:
    proc.terminate()
    sys.exit(0)