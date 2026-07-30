# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")


for ip in ${piIP[@]}; do
    echo "Copying and installing on $ip..."
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/python3-scapy_*.deb" &
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/python3-yaml_*.deb" &
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/chrony_*.deb" &
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/tcpdump_*.deb" &
done
wait
echo "Manual deployment complete!"