piIP=("192.168.0.244" "192.168.0.198")
piPath="/home/pi/scripts/RoutingScripts/Latency.py"

for host in ${piIP[@]}; do
    echo "Deploying to $ip"
    rsync -avz \
        --exclude '.git/' \
        --exclude '__pycache__/' \
        --exclude 'venv/' \
        --exclude '.env' \
        -e ssh \
        "$laptopPath" "pi@$pi:$piPath"
    done