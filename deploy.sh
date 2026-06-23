laptopIP = "192.168.0.190"
laptopUser = "IsaacO_P16"
laptopPath = "\Users\iolde\iCloud\iCloudDrive\School\Research\DrGeordon\Programs\RoutingScripts"
piIP = ("192.168.0.244" "192.168.0.198")

echo "Staging and committing changes to GitHub"
git add .
git commit -m "Updating Pi scripts"

for ip in ${piIP[@]}; do
    echo "Deploying to $ip"
    ssh pi@$ip "cd /home/RouterScripts && git pull ssh://laptopUser@$laptopIP$laptopPath main"
done