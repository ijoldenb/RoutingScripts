# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

scriptPath="/home/pi/scripts/Latency.py"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "nohup python3 $scriptPath > /dev/null 2>&1 &"

    echo "🚀 successfully started on $host"
done

echo "Commands Sent"