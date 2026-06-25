piIP=("192.168.0.244" "192.168.0.198")

for host in ${piIP[@]}; do
    ssh -n "pi@$host" sudo pkill -f Latency.py
    done

echo "Commands Sent"