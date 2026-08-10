#!/bin/bash

# Centralized configuration paths on the laptop
laptopPath="$HOME/RoutingScripts/"
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse target IPs from cluster config
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

# Calculate node count and VLAN upper bound LOCALLY on the laptop
numNodes=$(python3 -c "import yaml; data = yaml.safe_load(open('$yaml_file')); print(len(data.get('sim_ip', data)))")

vlan=$((numNodes + 100))

# Iterate through remote nodes
for host in "${piIP[@]}"; do
    echo "Configuring routes on $host..."

    # Pass local $vlan into remote script as argument $1 using quoted 'EOF'
    ssh "pi@$host" "sudo bash -s \"$vlan\"" << 'EOF'
        vlan_limit="$1"
        
        # Robustly extract IPv4 address from eth0 without regex backslash traps
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
                # 'replace' adds the route or updates it if it already exists
                ip route replace "$currentIPSubnet/24" dev eth0
                echo "Added/Updated route for $currentIPSubnet/24 via eth0"
            fi
        done
EOF

    echo "Success on $host"
done    

echo "Commands Sent"