laptopIP="192.168.0.243"
laptopUser="IsaacO_P16"
laptopPath="/home/ijoldenb/RoutingScripts/"
piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237" "192.168.0.129")
piPath="/home/pi/scripts/"

echo "Staging and committing changes to GitHub"
git add .
git commit -m "Updating Pi scripts"

for host in ${piIP[@]}; do
    echo "Deploying to $host"
    rsync -avz \
        --exclude '.git/' \
        --exclude '__pycache__/' \
        --exclude 'venv/' \
        --exclude '.env' \
        -e ssh \
        "$laptopPath" "pi@$host:$piPath"
    done