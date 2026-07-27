#!/bin/bash

# --- CONFIGURATION ---
# List of your Raspberry Pi IP addresses
piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")

# The local IP of your Main PC acting as the Chrony Server
MASTER_IP="192.168.0.243"

echo "=========================================================="
echo " Starting Automated Chrony Configuration on Pi Cluster"
echo "=========================================================="

for host in ${piIP[@]}; do
    echo "----------------------------------------------------------"
    echo "[*] Connecting to Pi: $host"
    echo "----------------------------------------------------------"

    # Execute configuration inline via SSH heredoc
    ssh -t "pi@$host" bash << EOF
        echo "[1/3] Disabling default systemd-timesyncd..."
        sudo systemctl disable --now systemd-timesyncd 2>/dev/null

        echo "[2/3] Modifying /etc/chrony/chrony.conf..."
        # Comment out existing generic pool and server entries
        sudo sed -i 's/^\(pool .*\)/#\1/g' /etc/chrony/chrony.conf
        sudo sed -i 's/^\(server .*\)/#\1/g' /etc/chrony/chrony.conf
        
        # Strip out any old entries matching this IP to prevent duplication if re-run
        sudo sed -i '/$MASTER_IP/d' /etc/chrony/chrony.conf

        # Append the explicit high-priority tracking configuration
        echo -e "\n# Local Master Cluster Sync\nserver $MASTER_IP iburst minpoll 2 maxpoll 4" | sudo tee -a /etc/chrony/chrony.conf

        echo "[3/3] Restarting Chrony daemon and forcing step sync..."
        sudo systemctl restart chrony
        sudo chronyc makestep

        echo -e "\n[*] VERIFICATION FOR $host:"
        sudo chronyc sources
        echo ""
EOF

    # Check if the SSH session executed cleanly
    if [ $? -eq 0 ]; then
        echo "[✓] Configuration successfully applied to $host"
    else
        echo "[✗] Connection or execution failure on $host"
    fi
done

echo "=========================================================="
echo " Configuration Engine Complete!"
echo "=========================================================="