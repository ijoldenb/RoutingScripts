piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")
scriptPath="/home/pi/scripts/packetTracer.py"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "sudo nohup python3 $scriptPath > /dev/null 2>&1 &"

    echo "🚀 successfully started on $host"
done

echo "Commands Sent"