local_ip = $(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

for i in {101..120}; do
    if i = $local_ip; then
        continue
    else
        ip route add 192.168.$i.0/24 dev eth0
    fi
done