piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")

for host in ${piIP[@]}; do
    ssh -n "pi@$host" sudo ptp4l -i eth0 -m -s -S
    echo "🚀 successfully started on $host"
done

echo "Commands Sent"