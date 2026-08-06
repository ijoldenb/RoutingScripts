#!/bin/bash

# Define path to the centralized configuration file
laptopPath="$HOME/RoutingScripts/"
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

scriptPath="/home/pi/scripts/ipRoute.sh"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "sudo nohup bash $scriptPath > /dev/null 2>&1 &"

    echo "success on $host"
done    

echo "Commands Sent"