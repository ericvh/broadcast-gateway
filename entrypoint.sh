#!/bin/bash
set -e

# Default values
UDP_PORT=${UDP_PORT:-50222}
TCP_PORT=${TCP_PORT:-8888}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0}
ENABLE_FIREWALL=${ENABLE_FIREWALL:-false}
FIREWALL_INTERFACE=${FIREWALL_INTERFACE:-any}

# Build command arguments
ARGS="--udp-port $UDP_PORT --tcp-port $TCP_PORT --bind-address $BIND_ADDRESS"

if [ "$ENABLE_FIREWALL" = "true" ]; then
    ARGS="$ARGS --enable-firewall"
    if [ "$FIREWALL_INTERFACE" != "any" ]; then
        ARGS="$ARGS --firewall-interface $FIREWALL_INTERFACE"
    fi
    
    # Check if we're running as root for firewall operations
    if [ "$(id -u)" != "0" ]; then
        echo "Warning: ENABLE_FIREWALL=true but not running as root. Firewall rules may not work."
    fi
fi

echo "Starting Multicast Gateway with args: $ARGS"

# Execute the Python gateway
exec python gateway.py $ARGS
