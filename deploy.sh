laptopIP="192.168.0.190"
laptopUser="IsaacO_P16"
laptopPath="/mnt/c/Users/iolde/iCloud/iCloudDrive/School/Research/DrGeordon/Programs/RoutingScripts"
piIP=("192.168.0.244" "192.168.0.198" "192.168.0.237")
piPath="/home/pi/scripts/"

echo "Staging and committing changes to GitHub"
git add .
git commit -m "Updating Pi scripts"

for host in ${piIP[@]}; do
    echo "Deploying to $ip"
    rsync -avz \
        --exclude '.git/' \
        --exclude '__pycache__/' \
        --exclude 'venv/' \
        --exclude '.env' \
        -e ssh \
        "$laptopPath" "pi@$host:$piPath"
    done