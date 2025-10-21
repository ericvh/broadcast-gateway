# Broadcast Gateway

A Kubernetes-ready UDP to TCP broadcast gateway service that listens for UDP broadcasts and forwards them to a connected TCP endpoint, with optional iptables firewall management.

## Overview

This service provides a bridge between UDP broadcast traffic and a TCP endpoint. It connects to a specified TCP host/port at startup and forwards all received UDP broadcasts to that endpoint. It's designed to run in Kubernetes with host networking to ensure proper access to the host's network interfaces for both UDP listening and firewall rule management.

## Features

- **UDP Broadcasting**: Listens for UDP broadcasts on a configurable port
- **TCP Forwarding**: Connects to a specified TCP endpoint and forwards all UDP messages
- **Automatic Reconnection**: Maintains connection with automatic retry on disconnection
- **Host Networking**: Uses Kubernetes host networking for proper network interface access
- **Firewall Management**: Optional iptables rule management for UDP port access
- **Health Checks**: Built-in liveness and readiness probes
- **Resource Efficient**: Lightweight Python implementation with minimal dependencies

## Project Structure

```
├── gateway.py                    # Main gateway service implementation
├── Dockerfile                    # Container build instructions
├── entrypoint.sh                # Container entrypoint script
├── requirements.txt              # Python dependencies
├── .github/workflows/            # GitHub CI/CD pipeline
├── k8s/                         # Kubernetes deployment manifests
│   ├── deployment.yaml          # Basic deployment
│   └── deployment-with-nodeport.yaml # Deployment with NodePort service
├── helm/broadcast-gateway/       # Helm chart
└── README.md, TODO.md, CHANGES.md, DEVELOPMENT.md # Documentation
```

## Quick Start

### Docker Run (Local Testing)

```bash
# Basic run - connecting to a TCP endpoint
docker run -d --name broadcast-gateway \
  --network host \
  --privileged \
  ghcr.io/ericvh/broadcast-gateway:latest \
  --tcp-host your-tcp-server.com

# With custom configuration
docker run -d --name broadcast-gateway \
  --network host \
  --privileged \
  ghcr.io/ericvh/broadcast-gateway:latest \
  --tcp-host your-tcp-server.com \
  --tcp-port 9999 \
  --udp-port 50222 \
  --enable-firewall
```

### Direct Python Execution

```bash
# Basic usage
python3 gateway.py --tcp-host your-tcp-server.com

# With full configuration
python3 gateway.py \
  --tcp-host your-tcp-server.com \
  --tcp-port 9999 \
  --udp-port 50222 \
  --bind-address 0.0.0.0 \
  --enable-firewall \
  --reconnect-delay 3.0
```

### Kubernetes Deployment

#### Using kubectl directly:

```bash
# Apply the basic deployment
kubectl apply -f k8s/deployment.yaml

# Or with NodePort for external access
kubectl apply -f k8s/deployment-with-nodeport.yaml
```

#### Using Helm:

```bash
# Add the chart (if publishing to a Helm repository)
helm repo add your-repo https://your-helm-repo.com
helm repo update

# Install with default values
helm install broadcast-gateway your-repo/broadcast-gateway

# Install with custom configuration
helm install broadcast-gateway your-repo/broadcast-gateway \
  --set network.udpPort=50222 \
  --set network.tcpPort=8888 \
  --set network.enableFirewall=true \
  --set service.type=NodePort
```

## Configuration

The gateway can be configured using command line arguments:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--tcp-host` | **Yes** | - | TCP host to connect to (required) |
| `--udp-port` | No | 50222 | UDP port to listen for broadcasts |
| `--tcp-port` | No | 8888 | TCP port to connect to |
| `--bind-address` | No | 0.0.0.0 | Address to bind UDP listener to |
| `--enable-firewall` | No | false | Enable iptables firewall rules |
| `--firewall-interface` | No | any | Network interface for firewall rules |
| `--reconnect-delay` | No | 5.0 | Delay between reconnection attempts (seconds) |

## Architecture

```
UDP Broadcasts → [Gateway Service] → TCP Endpoint
     Port 50222 →    (Connect &    →  host:port
                      Forward)
```

The service connects to a specified TCP endpoint at startup and forwards each received UDP broadcast message to that endpoint, maintaining connection health and automatically reconnecting if the connection is lost.

## Message Protocol

To preserve message boundaries when converting from UDP datagrams to TCP stream, the gateway uses a length-prefixed protocol:

**Format**: `[4-byte length][message data]`
- First 4 bytes: Message length in big-endian format (unsigned 32-bit integer)
- Remaining bytes: The original UDP datagram payload

### TCP Endpoint Implementation Example

To receive messages from the gateway, create a TCP server that accepts connections and reads the length-prefixed messages:

```python
import asyncio
import struct
from gateway import read_length_prefixed_message

async def handle_gateway_connection(reader, writer):
    """Handle connection from the broadcast gateway."""
    client_addr = writer.get_extra_info('peername')
    print(f"Gateway connected: {client_addr}")
    
    try:
        while True:
            # Read length-prefixed message
            message_data = await read_length_prefixed_message(reader)
            if message_data is None:
                break
            print(f"Received UDP broadcast: {message_data}")
            
            # Process the UDP message here
            # (e.g., send to other systems, store in database, etc.)
            
    except Exception as e:
        print(f"Error reading from gateway: {e}")
    finally:
        print(f"Gateway disconnected: {client_addr}")
        writer.close()
        await writer.wait_closed()

async def start_tcp_server():
    """Start TCP server to receive messages from gateway."""
    server = await asyncio.start_server(handle_gateway_connection, '0.0.0.0', 8888)
    print("TCP server listening on 0.0.0.0:8888")
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(start_tcp_server())
```

## Security Considerations

- The service requires `privileged: true` and host networking when using firewall features
- Firewall management requires root privileges (`runAsUser: 0`)
- Consider network policies for additional security in production

## Development

### Building the Docker Image

```bash
docker build -t broadcast-gateway:latest .
```

### Running Tests

```bash
# Test UDP to TCP forwarding locally
python3 gateway.py --udp-port 50222 --tcp-port 8888 --enable-firewall
```

## CI/CD

The project includes GitHub Actions for:
- Building multi-architecture Docker images (amd64, arm64)
- Pushing to GitHub Container Registry
- Security scanning with Trivy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update documentation and tests
5. Submit a pull request
