piIP=("192.168.0.244")
scriptPath="/home/pi/scripts/RoutingScripts/packetSend.py"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "nohup python3 $scriptPath > /dev/null 2>&1 &"
    done

    echo "🚀 successfully started on $host"

echo "Commands Sent"