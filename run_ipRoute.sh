#!/bin/bash

# Centralized configuration paths on the laptop
laptopPath="$HOME/RoutingScripts/"
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"
YAML_FILE="${laptopPath}sim_IP.yaml"

# Dynamically parse target IPs from cluster config
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

# 2. Parse 'sim_IP' length using Python
numNodes=$(python3 -c "import yaml; data = yaml.safe_load(open('$YAML_FILE')); print(len(data.get('sim_IP', data)))" 2>/dev/null)

vlan=$((numNodes + 100))
echo "Detected $numNodes nodes under 'sim_IP'. Setting VLAN upper bound to $vlan."

# Iterate through remote nodes
for host in "${piIP[@]}"; do
    echo "Configuring routes on $host..."

    # Pass local $vlan into remote script as argument $1 using quoted 'EOF'
    ssh "pi@$host" "sudo bash -s \"$vlan\"" << 'EOF'
        vlan_limit="$1"
        
        # Extract IPv4 address on eth0 safely
        local_ip=$(ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)

        if [ -z "$local_ip" ]; then
            echo "Warning: Could not detect IP on eth0 for this node."
        fi

        for i in $(seq 101 "$vlan_limit"); do
            currentIPSubnet="192.168.$i.0"
            currentIP="192.168.$i.10"

            if [ "$local_ip" = "$currentIP" ]; then
                echo "Skipping local subnet interface: $currentIPSubnet/24"
            else
                ip route replace "$currentIPSubnet/24" dev eth0
                echo "Added/Updated route for $currentIPSubnet/24 via eth0"
            fi
        done
        # Disable offloading on the Pi's main network interface (usually eth0)
        sudo ethtool -K eth0 tx off rx off tso off gso off gro off 2>/dev/null
EOF

    echo "Success on $host"
done    

echo "All commands executed successfully."