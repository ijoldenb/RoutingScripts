piIP=("192.168.0.244" "192.168.0.198")
scriptPath="/home/pi/scripts/RoutingScripts/Latency.py"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "nohup python3 $scriptPath > /dev/null 2>&1 &"

    echo "🚀 successfully started on $host"
done

echo "Commands Sent"