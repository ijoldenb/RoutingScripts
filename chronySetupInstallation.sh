#!/bin/bash

laptopPath="/home/ijoldenb/RoutingScripts/"

# Main PC Setup
# Disable the modern default systemd client
sudo systemctl disable --now systemd-timesyncd
sudo systemctl disable --now ntp 2>/dev/null || true
sudo apt purge -y systemd-timesyncd ntp openntpd
sudo rm -f /etc/dhcp/dhclient-exit-hooks.d/timesyncd

sudo apt install chrony

# Remote Pi Setup

# Define path to the centralized configuration file
CLUSTER_CONFIG="${laptopPath}control_IP.yaml"
# Dynamically parse out the IP addresses from the PI_CLUSTER dictionary format
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")

for ip in ${piIP[@]}; do
    ssh pi@$ip "sudo systemctl disable --now systemd-timesyncd"
    ssh pi@$ip "sudo systemctl disable --now ntp 2>/dev/null || true"
    ssh pi@$ip "sudo apt purge -y systemd-timesyncd ntp openntpd"
    ssh pi@$ip "sudo rm -f /etc/dhcp/dhclient-exit-hooks.d/timesyncd"

    ssh pi@$ip "sudo dpkg -i /home/pi/scripts/chrony*.deb"
done
