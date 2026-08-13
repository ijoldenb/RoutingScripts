laptopIP="192.168.0.243"
laptopUser="IsaacO_P16"
laptopPath="$HOME/RoutingScripts/"
piPath="/home/pi/scripts/"

# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for ip in "${piIP[@]}"; do
    echo -n "Deploying Chrony to $ip... "
    
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "pi@$ip" "
        sudo systemctl disable --now systemd-timesyncd 2>/dev/null || true
        sudo systemctl disable --now ntp 2>/dev/null || true
        sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y systemd-timesyncd ntp openntpd >/dev/null 2>&1 || true
        
        # Ensure chrony is installed
        sudo DEBIAN_FRONTEND=noninteractive dpkg -i /home/pi/scripts/chrony*.deb >/dev/null 2>&1 || sudo apt-get install -y chrony >/dev/null 2>&1
        
        # Append server config directly to chrony.conf with fast polling options
        sudo sed -i '/server /d' /etc/chrony/chrony.conf
        sudo grep -qxF 'server ${MAIN_PC_IP} minpoll 0 maxpoll 2 iburst' /etc/chrony/chrony.conf || echo 'server ${MAIN_PC_IP} minpoll 0 maxpoll 2 iburst' | sudo tee -a /etc/chrony/chrony.conf >/dev/null
        
        # Restart and force step synchronization
        sudo systemctl restart chrony
        sleep 1
        sudo chronyc makestep >/dev/null 2>&1
    "
    echo "[DONE]"
done

echo "Commands Sent"