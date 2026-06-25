import socket
import json
import subprocess
import sys
import os

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

def detect_interface():
    """Finds if the local Pi uses eth0 or end0 automatically"""
    interfaces = os.listdir('/sys/class/net/')
    if 'eth0' in interfaces: return 'eth0'
    if 'end0' in interfaces: return 'end0'
    return 'eth0'

NETWORK_INTERFACE = detect_interface()

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def init_tc_interface():
    """Resets interface and alters the default priomap"""
    run_cmd(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root")
    
    # CRITICAL FIX: We tell the prio queue to default ALL unclassified traffic 
    # to band 3 (the 4th lane), leaving lanes 0, 1, and 2 purely for our custom delays.
    run_cmd(f"sudo tc qdisc add dev {NETWORK_INTERFACE} root handle 1: prio bands 4 priomap 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3")

def update_latencies(latency_map):
    # Wipe old rules before applying the new matrix payload
    init_tc_interface()
    
    # We map our delays starting at lane index 0 (Band 1)
    band_id = 0 
    for target_ip, target_delay in latency_map.items():
        if band_id > 2:
            print("Error: This test build supports up to 3 simultaneous targets per Pi.")
            break
            
        handle_id = (band_id + 1) * 10
        print(f"Python executing rule -> Dest: {target_ip} to Lane {band_id} ({target_delay}ms)")
        
        # 1. Inject the latency into the targeted lane
        run_cmd(f"sudo tc qdisc add dev {NETWORK_INTERFACE} parent 1:{band_id + 1} handle {handle_id}: netem delay {target_delay}ms")
        
        # 2. Add the u32 classifier filter linking the target IP to that lane
        run_cmd(f"sudo tc filter add dev {NETWORK_INTERFACE} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip} flowid 1:{band_id + 1}")
        
        band_id += 1

def main():
    print(f"Targeting network interface: {NETWORK_INTERFACE}")
    init_tc_interface()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Pi Agent online. Awaiting variable pushes from laptop...\n")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            latency_map = json.loads(data.decode('utf-8'))
            update_latencies(latency_map)
        except KeyboardInterrupt:
            print("\nCleaning up interface...")
            run_cmd(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root")
            sys.exit(0)

if __name__ == "__main__":
    main()