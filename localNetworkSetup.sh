#!/bin/bash
set -e

# 1. Root check must be FIRST before resolving paths or running commands
if [ "$EUID" -ne 0 ]; then
  echo "CRITICAL ERROR: Please run as root (sudo)."
  exit 1
fi

# --- CONFIGURATION BAR ---
# Target the actual user who invoked sudo (not /root)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

laptopPath="${REAL_HOME}/RoutingScripts/"
YAML_FILE="${laptopPath}sim_IP.yaml"
PHYS_NIC="enp0s31f6"

# Guard check: Ensure YAML file exists
if [ ! -f "$YAML_FILE" ]; then
    echo "CRITICAL ERROR: File not found at $YAML_FILE"
    exit 1
fi

# Run Python without 2>/dev/null so error messages are visible if it fails
NUM_NODES=$(python3 -c "import yaml; data = yaml.safe_load(open('$YAML_FILE')); print(len(data.get('sim_IP', data)))")
# --------------------------------------------------------------

echo "=== [1/2] Initializing Physical Hardware: $PHYS_NIC ==="
ip link set dev "$PHYS_NIC" up
ip link set dev "$PHYS_NIC" promisc on
echo "Success: Physical link optimized."
echo ""
# Disable offloading on physical NIC
sudo ethtool -K enp0s31f6 tx off rx off gso off tso off gro off

echo "=== [2/2] Provisioning $NUM_NODES Dynamic VLAN Interfaces ==="
for ((i=1; i<=NUM_NODES; i++)); do
    VLAN_ID=$((100 + i))
    VLAN_NAME="vlan${VLAN_ID}"
    
    echo "  -> Processing Node $i | Mapping to $VLAN_NAME..."
    
    # 1. Strip away old interface components
    ip link delete dev "$VLAN_NAME" 2>/dev/null || true
    
    # 2. Create raw VLAN interface on the hardware link
    ip link add link "$PHYS_NIC" name "$VLAN_NAME" type vlan id "$VLAN_ID"
    
    # 3. Bring up and enable promiscuous mode
    ip link set dev "$VLAN_NAME" up
    ip link set dev "$VLAN_NAME" promisc on

    sudo ethtool -K "$VLAN_NAME" tx off rx off gso off tso off gro off 2>/dev/null || true
    
    echo "     Status: $VLAN_NAME active."
done

echo ""
echo "===================================================="
echo " Network Infrastructure Setup Complete!"
echo "===================================================="