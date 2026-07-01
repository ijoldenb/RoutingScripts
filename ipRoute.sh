local_ip=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

for i in $(seq 101 120); do
    currentIP="192.168.$i.0"
    if [ "$local_ip" = "$currentIP" ]; then
        echo "Skipping local subnet interface: $currentIP/24"
        continue
    else
        ip route add "$currentIP/24" dev eth0
        echo "Added route for $currentIP/24 via eth0"
    fi
done
