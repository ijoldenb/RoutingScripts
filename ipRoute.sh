local_ip=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

for i in {101..120}; do
    if ["$local_ip" = "192.168.$i.0"]; then
        echo "Skipping local subnet interface: 192.168.$i.0/24"
        continue
    else
        ip route add 192.168.$i.0/24 dev eth0
    fi
done