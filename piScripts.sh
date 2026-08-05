laptopIP="192.168.0.243"
laptopUser="IsaacO_P16"
laptopPath="/home/ijoldenb/RoutingScripts/"
piPath="/home/pi/scripts/"

# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "rm -r /home/pi/*.txt"
done

echo "Commands Sent"