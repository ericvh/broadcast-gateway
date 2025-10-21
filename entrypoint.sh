#!/bin/bash
set -e

# Default values
UDP_PORT=${UDP_PORT:-50222}
TCP_HOST=${TCP_HOST}
TCP_PORT=${TCP_PORT:-50222}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0}
ENABLE_FIREWALL=${ENABLE_FIREWALL:-false}
FIREWALL_INTERFACE=${FIREWALL_INTERFACE:-any}
RECONNECT_DELAY=${RECONNECT_DELAY:-5.0}

# Check required parameter
if [ -z "$TCP_HOST" ]; then
    echo "Error: TCP_HOST environment variable is required"
    echo "Usage: Set TCP_HOST to the hostname or IP address to connect to"
    exit 1
fi

# Build command arguments
ARGS="--udp-port $UDP_PORT --tcp-host $TCP_HOST --tcp-port $TCP_PORT --bind-address $BIND_ADDRESS"

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

# Add reconnect delay if set
if [ "$RECONNECT_DELAY" != "5.0" ]; then
    ARGS="$ARGS --reconnect-delay $RECONNECT_DELAY"
fi

echo "Starting Broadcast Gateway with args: $ARGS"

# Execute the Python gateway
exec python gateway.py $ARGS
