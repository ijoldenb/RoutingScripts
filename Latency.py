import socket
import json
import subprocess
import sys

UDP_IP = "0.0.0.0"  # Listen on all local interfaces
UDP_PORT = 5005

def run_cmd(cmd):
    """Helper to execute system shell commands safely"""
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        pass # Handle cases where a rule deletion fails because it didn't exist yet

def init_tc_interface(interface="eth0"):
    """Reset tc and create a root priority queueing discipline (prio)"""
    print(f"Initializing {interface} traffic control root...")
    run_cmd(f"sudo tc qdisc del dev {interface} root")
    # Create a root prio qdisc with 4 bands (0, 1, 2, 3)
    run_cmd(f"sudo tc qdisc add dev {interface} root handle 1: prio bands 4")

def update_latencies(interface, latency_map):
    """
    latency_map structure: {"10.0.0.2": 45.2, "10.0.0.3": 120.1}
    Where keys are target IPs and values are the required delay in milliseconds.
    """
    # 1. Clear existing child queues/filters by re-initializing the root
    init_tc_interface(interface)
    
    # 2. Dynamically bind target IPs to specific delay bands
    # Band 1 (handle 10:), Band 2 (handle 20:), etc.
    band_id = 1
    for target_ip, target_delay in latency_map.items():
        if band_id > 3:
            print("Warning: Exceeded available tc priority bands!")
            break
            
        handle_id = band_id * 10
        
        # Attach a netem delay rule to this specific priority band channel
        print(f"Binding {target_ip} to Band {band_id} with {target_delay}ms delay")
        run_cmd(f"sudo tc qdisc add dev {interface} parent 1:{band_id} handle {handle_id}: netem delay {target_delay}ms")
        
        # Create an IP filter routing traffic destined for target_ip into this band
        run_cmd(f"sudo tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip} flowid 1:{band_id}")
        
        band_id += 1

def main():
    interface = "eth0" # Change if using a USB-Ethernet adapter or wlan0
    init_tc_interface(interface)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Pi Agent listening for orbital latency updates on port {UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            # Expects a JSON string representing target node delays
            latency_map = json.loads(data.decode('utf-8'))
            update_latencies(interface, latency_map)
        except Exception as e:
            print(f"Error parsing or applying update: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()