# Multicast Gateway

A Kubernetes-ready UDP to TCP multicast gateway service that listens for UDP broadcasts and relays them to TCP clients, with optional iptables firewall management.

## Overview

This service provides a bridge between UDP broadcast traffic and TCP clients. It's designed to run in Kubernetes with host networking to ensure proper access to the host's network interfaces for both UDP listening and firewall rule management.

## Features

- **UDP Broadcasting**: Listens for UDP broadcasts on a configurable port
- **TCP Relaying**: Forwards received UDP messages to all connected TCP clients
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
├── helm/multicast-gateway/       # Helm chart
└── README.md, TODO.md, CHANGES.md # Documentation
```

## Quick Start

### Docker Run (Local Testing)

```bash
# Basic run with default ports
docker run -d --name multicast-gateway \
  --network host \
  --privileged \
  ghcr.io/your-username/multicast-gateway:latest

# With custom ports and firewall enabled
docker run -d --name multicast-gateway \
  --network host \
  --privileged \
  -e UDP_PORT=50222 \
  -e TCP_PORT=8888 \
  -e ENABLE_FIREWALL=true \
  ghcr.io/your-username/multicast-gateway:latest
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
helm install multicast-gateway your-repo/multicast-gateway

# Install with custom configuration
helm install multicast-gateway your-repo/multicast-gateway \
  --set network.udpPort=50222 \
  --set network.tcpPort=8888 \
  --set network.enableFirewall=true \
  --set service.type=NodePort
```

## Configuration

The gateway can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `UDP_PORT` | 50222 | UDP port to listen for broadcasts |
| `TCP_PORT` | 8888 | TCP port for client connections |
| `BIND_ADDRESS` | 0.0.0.0 | Address to bind services to |
| `ENABLE_FIREWALL` | false | Enable iptables firewall rules |
| `FIREWALL_INTERFACE` | any | Network interface for firewall rules |

## Architecture

```
UDP Broadcasts → [Gateway Service] → TCP Clients
     Port 50222 →     (Relay)      →  Port 8888
```

The service maintains a list of connected TCP clients and forwards each received UDP broadcast message to all connected clients simultaneously.

## Security Considerations

- The service requires `privileged: true` and host networking when using firewall features
- Firewall management requires root privileges (`runAsUser: 0`)
- Consider network policies for additional security in production

## Development

### Building the Docker Image

```bash
docker build -t multicast-gateway:latest .
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
