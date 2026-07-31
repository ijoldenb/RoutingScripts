# Path to the centralized YAML configuration file
CLUSTER_CONFIG="${laptopPath}pi_cluster.yaml"

# Parse out the IP addresses from the YAML file structure natively
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for host in ${piIP[@]}; do
    ssh -n "pi@$host" sudo pkill -f Latency.py
    echo "🚀 successfully killed on $host"
done

echo "Commands Sent"