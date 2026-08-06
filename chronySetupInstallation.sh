#!/bin/bash
set -e

# --- CONFIGURATION ---
laptopPath="$HOME/RoutingScripts/"
MAIN_PC_IP="192.168.0.243"

CLUSTER_CONFIG="${laptopPath}control_IP.yaml"
# ---------------------

if [ "$EUID" -ne 0 ]; then
  echo "CRITICAL ERROR: Please run as root (sudo) on the Main PC."
  exit 1
fi

echo "=== [1/2] Configuring Local Main PC (Time Master) ==="
sudo systemctl disable --now systemd-timesyncd 2>/dev/null || true
sudo systemctl disable --now ntp 2>/dev/null || true

sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y systemd-timesyncd ntp openntpd >/dev/null 2>&1 || true
sudo rm -f /etc/dhcp/dhclient-exit-hooks.d/timesyncd

sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq chrony

# Inject the permanent allow rule into the drop-in folder
sudo mkdir -p /etc/chrony/conf.d
echo "allow 192.168.0.0/24" | sudo tee /etc/chrony/conf.d/simulation.conf >/dev/null
sudo systemctl restart chrony
echo "Main PC Setup Complete."
echo ""

echo "=== [2/2] Provisioning Remote Pis via SSH ==="
if [ ! -f "$CLUSTER_CONFIG" ]; then
  echo "CRITICAL ERROR: Configuration file '$CLUSTER_CONFIG' not found."
  exit 1
fi

# Dynamically parse out IP addresses
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for ip in "${piIP[@]}"; do
    echo -n "Deploying Chrony to $ip... "
    
    # -o StrictHostKeyChecking=no suppresses host verification prompts
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "pi@$ip" "
        sudo systemctl disable --now systemd-timesyncd 2>/dev/null || true
        sudo systemctl disable --now ntp 2>/dev/null || true
        
        sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y systemd-timesyncd ntp openntpd >/dev/null 2>&1 || true
        sudo rm -f /etc/dhcp/dhclient-exit-hooks.d/timesyncd
        
        # Install the deb package silently with noninteractive sudo
        sudo DEBIAN_FRONTEND=noninteractive dpkg -i /home/pi/scripts/chrony*.deb >/dev/null 2>&1
        
        # Create persistent source pointing back to the Main PC
        sudo mkdir -p /etc/chrony/sources.d
        echo 'server ${MAIN_PC_IP} minpoll 2 maxpoll 4 iburst' | sudo tee /etc/chrony/sources.d/master-pc.sources >/dev/null
        
        # Restart and force immediate time stepping alignment
        sudo systemctl restart chrony
        sudo chronyc makestep >/dev/null 2>&1
    "
    echo "[DONE]"
done

echo ""
echo "===================================================="
echo " Total Cluster Chrony Synchronization Complete!"
echo "===================================================="