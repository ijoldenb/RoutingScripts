import socket
import json
import os
import sys
import subprocess
import signal  # <-- Crucial addition

NETWORK_INTERFACE = "eth0"

def clean_exit():
    """The one-stop shop for restoring the network card"""
    print(f"\n[OS CLEANUP] Restoring default fq_codel network queue on {NETWORK_INTERFACE}...", flush=True)
    os.system(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root 2>/dev/null")

def os_signal_handler(signum, frame):
    """Catches OS termination signals (like IDE stop buttons or kill commands)"""
    print(f"\n[SIGNAL DETECTED] Script caught signal {signum}", flush=True)
    clean_exit()
    sys.exit(0)

# ==============================================================================
# REGISTER THE OS BOTTLENECKS
# ==============================================================================
# Catch standard termination (IDE Stop buttons, standard 'kill' commands)
signal.signal(signal.SIGTERM, os_signal_handler)
# Catch terminal closures (If you close the SSH window while it's running)
signal.signal(signal.SIGHUP, os_signal_handler)

def update_latencies(latency_map):
    subprocess.run(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root", shell=True, capture_output=True)
    target_delay = list(latency_map.values())[0]
    print(f"Applying GLOBAL Interface Delay -> {target_delay}ms", flush=True)
    os.system(f"sudo tc qdisc add dev {NETWORK_INTERFACE} root netem delay {target_delay}ms")

def main():
    print(f"Targeting network interface: {NETWORK_INTERFACE}", flush=True)
    
    # Initialize a clean slate on boot
    os.system(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root 2>/dev/null")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 65000)) # Listens on all interfaces
    print(f"Pi Agent online. Awaiting variable pushes...\n", flush=True)

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            latency_map = json.loads(data.decode('utf-8'))
            update_latencies(latency_map)
            print("Doing Stuff", flush=True)
            
    except KeyboardInterrupt:
        # Catch standard Ctrl+C in terminal
        clean_exit()
        sys.exit(0)

if __name__ == "__main__":
    main()