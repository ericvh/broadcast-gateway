# Change Log

This document tracks all changes, implementations, and modifications made to the multicast gateway project.

## [v1.0.0] - 2024-12-19

### Added
- **Core Gateway Service** (`gateway.py`):
  - UDP broadcast listener with configurable port and binding address
  - TCP server for client connections with automatic connection management
  - Asynchronous message forwarding from UDP to all connected TCP clients
  - Graceful shutdown handling with signal management
  - Comprehensive logging and error handling

- **Firewall Management**:
  - Optional iptables rule management for UDP port access
  - Automatic rule cleanup on service shutdown
  - Support for specific network interface targeting
  - Root privilege detection and warnings

- **Containerization** (`Dockerfile`):
  - Multi-stage Python 3.11 slim-based image
  - System dependencies for iptables and networking tools
  - Non-root user support with privilege escalation for firewall features
  - Health check integration
  - Configurable runtime environment variables

- **Kubernetes Deployment** (`k8s/`):
  - Basic deployment with ClusterIP service
  - NodePort deployment for external access
  - Host networking configuration for proper interface access
  - Privileged security context for firewall operations
  - Resource limits and health probes

- **Helm Chart** (`helm/multicast-gateway/`):
  - Complete Helm chart with configurable values
  - Template-based deployment and service definitions
  - Support for various service types (ClusterIP, NodePort)
  - Customizable network and security settings
  - Installation notes and guidance

- **CI/CD Pipeline** (`.github/workflows/`):
  - Multi-architecture Docker image building (amd64, arm64)
  - Automated security scanning with Trivy
  - GitHub Container Registry integration
  - Tag-based versioning support

- **Documentation**:
  - Comprehensive README with usage examples
  - Configuration reference and architecture diagrams
  - Security considerations and development guidelines

### Technical Details
- **Language**: Python 3.11 using asyncio for concurrent operations
- **Networking**: Host networking mode with UDP broadcast reception
- **Dependencies**: Zero external Python dependencies (standard library only)
- **Security**: Privileged container support with root access for firewall management
- **Deployment**: Kubernetes-native with host networking and proper resource management

### Configuration
- **Default Ports**: UDP 9999, TCP 8888
- **Environment Variables**: Full configuration via environment variables
- **Firewall**: Optional iptables integration with interface-specific rules

## [Initial Setup] - 2024-12-19

### Added
- Basic project documentation structure:
  - `README.md` - Project overview and setup instructions
  - `TODO.md` - Task tracking and development roadmap  
  - `CHANGES.md` - This change log

### Changes
- Initialized project with essential documentation files

### Technical Details
- Created minimal documentation framework to support development workflow
- Established change tracking methodology for future modifications
