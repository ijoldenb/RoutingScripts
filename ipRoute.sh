local_ip=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

laptopPath="$HOME/RoutingScripts/"
yaml_file="${laptopPath}sim_IP.yaml"
# Evaluates 'sim_ip' if it exists, otherwise falls back to the root object (.), then gets the length
numNodes=$(yq '(.sim_ip // .) | length' "$yaml_file")
vlan="$(($numNodes + 100))"

for i in $(seq 101 $vlan); do
    currentIPSubnet="192.168.$i.0"
    currentIP="192.168.$i.10"
    if [ "$local_ip" = "$currentIP" ]; then
        echo "Skipping local subnet interface: $currentIPSubnet/24"
        continue
    else
        ip route add "$currentIPSubnet/24" dev eth0
        echo "Added route for $currentIPSubnet/24 via eth0"
    fi
done