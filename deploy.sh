laptopPath="~/RoutingScripts/"
piPath="/home/pi/scripts/"

# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"

# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

echo "Staging and committing changes to GitHub"
git add .
git commit -m "Updating Pi scripts"

for host in ${piIP[@]}; do
    ssh -n "pi@$host" "rm -r /home/pi/scripts/*"
done

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