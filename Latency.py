import socket
import json
import subprocess
import sys
import os

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

NETWORK_INTERFACE = "eth0"

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
    subprocess.run(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root", shell=True, capture_output=True)
  
    # (Grabs the first delay value found in the incoming laptop dictionary)
    target_delay = list(latency_map.values())[0]
    
    print(f"Applying GLOBAL Interface Delay -> {target_delay}ms on {NETWORK_INTERFACE}")
    
    run_cmd(f"sudo tc qdisc add dev {NETWORK_INTERFACE} root netem delay {target_delay}ms")

def main():
    print(f"Targeting network interface: {NETWORK_INTERFACE}")
    init_tc_interface()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Pi Agent online. Awaiting variable pushes from laptop...\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            latency_map = json.loads(data.decode('utf-8'))
            update_latencies(latency_map)
            print("Doing Stuff", flush=True)
            
    except KeyboardInterrupt:
        print("\nUser requested stop. Exiting...", flush=True)
        
    finally:
        # 3. This block will ALWAYS run, even if the script crashes or gets closed!
        print("\n[SAFETY CLEANUP] Restoring default fq_codel network queue...", flush=True)
        # Suppress errors with 2>/dev/null in case it was already deleted
        os.system(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root 2>/dev/null")

if __name__ == "__main__":
    main()