import socket
import json
import subprocess
import sys

UDP_IP = "0.0.0.0"  # Listen on all local interfaces
UDP_PORT = 5005
NETWORK_INTERFACE = "eth0" # Change to match your active interface (e.g., eth0, wlan0)

def run_cmd(cmd):
    """Executes system shell commands safely"""
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass # Ignore deletion errors for non-existent rules

def init_tc_interface():
    """Reset tc and create a fresh 4-band priority queuing root"""
    print(f"Resetting {NETWORK_INTERFACE} queue configurations...")
    run_cmd(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root")
    run_cmd(f"sudo tc qdisc add dev {NETWORK_INTERFACE} root handle 1: prio bands 4")

def update_latencies(latency_map):
    """Clears old queues and maps target IPs to latency bands"""
    init_tc_interface()
    
    band_id = 1
    for target_ip, target_delay in latency_map.items():
        if band_id > 3:
            print("Error: Running out of priority bands! Maximum 3 targets supported per Pi in this test.")
            break
            
        handle_id = band_id * 10
        print(f"Applying rule: Dest IP {target_ip} -> Delaying {target_delay}ms")
        
        # 1. Attach the specific latency delay to this band lane
        run_cmd(f"sudo tc qdisc add dev {NETWORK_INTERFACE} parent 1:{band_id} handle {handle_id}: netem delay {target_delay}ms")
        
        # 2. Filter target IP packets into this specific lane
        run_cmd(f"sudo tc filter add dev {NETWORK_INTERFACE} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip} flowid 1:{band_id}")
        
        band_id += 1

def main():
    # Initial setup step
    init_tc_interface()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"\nPi Agent successfully running on port {UDP_PORT}. Waiting for laptop variables...")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            latency_map = json.loads(data.decode('utf-8'))
            print("\nReceived configuration matrix update.")
            update_latencies(latency_map)
        except KeyboardInterrupt:
            print("\nCleaning up interface before exiting...")
            run_cmd(f"sudo tc qdisc del dev {NETWORK_INTERFACE} root")
            sys.exit(0)
        except Exception as e:
            print(f"Error handling configuration payload: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()