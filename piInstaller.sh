for ip in 192.168.0.244 192.168.0.198 192.168.0.129 192.168.0.237; do
    echo "Copying and installing on $ip..."
    scp /home/ijoldenb/Downloads/python3-scapy_*.deb pi@$ip:~
    ssh pi@$ip "sudo dpkg -i ~/python3-scapy_*.deb" &
done
wait
echo "Manual deployment complete!"