# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")


for ip in ${piIP[@]}; do
    echo "Copying and installing on $ip..."
    scp /home/ijoldenb/RoutingScripts/python3-scapy_*.deb pi@$ip:~
    scp /home/ijoldenb/RoutingScripts/python3-yaml_*.deb pi@$ip:~
    scp /home/ijoldenb/RoutingScripts/chrony_*.deb pi@$ip:~
    
    ssh pi@$ip "sudo dpkg -i ~/python3-scapy_*.deb" &
    ssh pi@$ip "sudo dpkg -i ~/python3-yaml_*.deb" &
    ssh pi@$ip "sudo dpkg -i ~/chrony_*.deb" &
done
wait
echo "Manual deployment complete!"