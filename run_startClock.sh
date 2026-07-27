#!/bin/bash

piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")
scriptPath="/home/pi/scripts/RoutingScripts/startClock.sh"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "nohup bash $scriptPath > /dev/null 2>&1 &"

    echo "success on $host"
done    

echo "Commands Sent"