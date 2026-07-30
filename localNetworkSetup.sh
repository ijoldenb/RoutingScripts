#!/bin/bash
set -e

# --- CONFIGURATION BAR ---
PHYS_NIC="enp0s31f6" # Set this to your physical network interface for the simulation network
SIM_CONFIG="sim_IP.yaml" # Path to your simulation IP configuration file
NUM_NODES=$(grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' "$SIM_CONFIG" | wc -l)  # Set this to your 'x' value
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