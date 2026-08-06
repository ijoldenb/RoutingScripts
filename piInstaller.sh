# Define path to the centralized configuration file
laptopPath="$HOME/RoutingScripts/"
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for ip in ${piIP[@]}; do
    echo "installing on $ip..."
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/Packages/libiperf0_*.deb"
done

for ip in ${piIP[@]}; do
    echo "installing on $ip..."
    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/Packages/*.deb"
done
wait
echo "Manual deployment complete!"