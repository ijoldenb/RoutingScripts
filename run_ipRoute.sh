#!/bin/bash

piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237")
scriptPath="/home/pi/scripts/RoutingScripts/ipRoute.sh"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "sudo ./$scriptPath > /dev/null 2>&1 &"

    echo "success on $host"
done    

echo "Commands Sent"