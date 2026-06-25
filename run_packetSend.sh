piIP=("192.168.0.244")
scriptPath="/home/pi/scripts/RoutingScripts/packetSend.py"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "nohup python3 $scriptPath > /dev/null 2>&1 &"
    done

    if [ $? -eq 0 ]; then
        echo "🚀 successfully started on $host"
    else
        echo "❌ Failed to trigger script on $host"
    fi
echo "Commands Sent"