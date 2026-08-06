#!/bin/bash
set -e

laptopPath="~/RoutingScripts/"
MAIN_PC_IP="192.168.0.243"
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"


echo "=== [1/2] Configuring Local Main PC (Time Master) ==="

# 1. Ensure 'allow' and 'local stratum' are present in the main chrony.conf
grep -qF "allow 192.168.0.0/24" /etc/chrony/chrony.conf || echo "allow 192.168.0.0/24" | sudo tee -a /etc/chrony/chrony.conf >/dev/null
grep -qF "local stratum 10" /etc/chrony/chrony.conf     || echo "local stratum 10"     | sudo tee -a /etc/chrony/chrony.conf >/dev/null

# 2. Open UDP port 123 on UFW firewall
sudo ufw allow from 192.168.0.0/24 to any port 123 proto udp >/dev/null 2>&1 || sudo ufw allow 123/udp >/dev/null 2>&1

# 3. Restart Chrony to apply changes and bind UDP port 123
sudo systemctl restart chrony
echo "Main PC Chrony configured and listening on UDP port 123."
echo ""

echo "=== [2/2] Configuring Remote Pis ==="

if [ ! -f "$CLUSTER_CONFIG" ]; then
  echo "CRITICAL ERROR: Configuration file '$CLUSTER_CONFIG' not found."
  exit 1
fi

# Dynamically parse out the IP addresses from your YAML file
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for ip in "${piIP[@]}"; do
    echo -n "Configuring Chrony on node $ip... "
    
    # Run all remote tasks in a single SSH connection
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "pi@$ip" "
        sudo mkdir -p /etc/chrony/sources.d
        echo 'server ${MAIN_PC_IP} minpoll 2 maxpoll 4 iburst' | sudo tee /etc/chrony/sources.d/master-pc.sources >/dev/null
        sudo systemctl restart chrony
        sudo chronyc makestep >/dev/null 2>&1
    "
    echo "[DONE]"
done

echo ""
echo "===================================================="
echo " Chrony Setup Complete Across All Nodes!"
echo "===================================================="