piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")

for host in ${piIP[@]}; do
    ssh -n "pi@$host" sudo pkill -f packetTracer.py
    echo "🚀 successfully killed on $host"
done

echo "Commands Sent"