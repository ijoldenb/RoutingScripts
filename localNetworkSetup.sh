#!/bin/bash
set -e

# --- CONFIGURATION BAR ---
# Fallback to $USER if SUDO_USER is not set (i.e., when run without sudo)
REAL_USER="${SUDO_USER:-$USER}"

# Expand the home directory of that specific user
REAL_HOME=$(eval echo "~$REAL_USER")

laptopPath="$REAL_HOME/RoutingScripts/"
PHYS_NIC="enp0s31f6" # Set this to your physical network interface for the simulation network
CLUSTER_CONFIG="${laptopPath}sim_IP.yaml"
mapfile -t piIP < <(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$CLUSTER_CONFIG")
NUM_NODES=$(python3 -c "import yaml; data = yaml.safe_load(open('$C')); print(len(data.get('sim_IP', data)))" 2>/dev/null)
# -------------------------

if [ "$EUID" -ne 0 ]; then
  echo "CRITICAL ERROR: Please run as root (sudo)."
  exit 1
fi

echo "=== [1/2] Initializing Physical Hardware: $PHYS_NIC ==="
ip link set dev "$PHYS_NIC" up
ip link set dev "$PHYS_NIC" promisc on
echo "Success: Physical link optimized."
echo ""

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
    
    echo "     Status: $VLAN_NAME active."
done

echo ""
echo "===================================================="
echo " Network Infrastructure Setup Complete!"
echo "===================================================="