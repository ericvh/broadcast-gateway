# Change Log

This document tracks all changes, implementations, and modifications made to the broadcast gateway project.

## [v1.1.4] - 2024-12-19

### Fixed
- **TCP Connection Stability**: Improved connection management to prevent repeated disconnections
  - Replaced problematic connection monitoring that was causing frequent reconnections
  - Implemented cleaner connection watcher that only detects actual connection closure
  - Enhanced error handling in message forwarding to properly handle connection errors
  - Reduced timeout from 10 seconds to 1 second for faster connection closure detection

### Technical Details
- Connection monitoring now uses a simple watcher that only breaks when connection actually closes
- Better exception handling for ConnectionResetError, ConnectionAbortedError, and BrokenPipeError
- Improved `_drain_writer_safe` method with proper connection error handling
- Eliminated race conditions in connection state management

## [v1.1.3] - 2024-12-19

### Changed
- **Default TCP Port**: Changed default TCP port from 8888 to 50222
  - Updated gateway.py argument parser default value
  - Updated entrypoint.sh environment variable default
  - Updated Dockerfile EXPOSE and ENV TCP_PORT
  - Updated Kubernetes deployment manifests for container ports and health checks
  - Updated Helm chart values and health check configurations
  - Updated README.md configuration table and examples
  - Updated CHANGES.md default port documentation

### Technical Details
- Both UDP listening port and default TCP connection port now use 50222
- Maintains consistency across all deployment configurations
- Updated NodePort from 30888 to 30222 in deployment-with-nodeport.yaml

## [v1.1.2] - 2024-12-19

### Changed
- **Project Naming**: Renamed all references from `multicast-gateway` to `broadcast-gateway`
  - Updated all Kubernetes deployment manifests and service names
  - Updated Helm chart name, directory, and all template references
  - Updated Docker image references and container names in examples
  - Updated documentation, logging, and code comments
  - Renamed Helm chart directory from `helm/multicast-gateway/` to `helm/broadcast-gateway/`

### Technical Details
- All instances of "multicast-gateway" replaced with "broadcast-gateway"
- Updated project title and descriptions throughout codebase
- Maintained backward compatibility for existing deployments through environment variables

## [v1.1.1] - 2024-12-19

### Fixed
- **UDPProtocol Error**: Fixed missing `connection_made` and `connection_lost` methods in UDPProtocol class
  - UDPProtocol now properly inherits from `asyncio.DatagramProtocol`
  - Added required protocol methods that asyncio expects for datagram transports
  - Resolves error: `'UDPProtocol' object has no attribute 'connection_made'`

### Technical Details
- UDPProtocol class now implements the complete DatagramProtocol interface
- Added proper connection lifecycle management for UDP transport

## [v1.1.0] - 2024-12-19

### Changed
- **Architecture**: Changed from server mode to client mode - gateway now connects to TCP endpoints instead of accepting connections
  - Added required `--tcp-host` parameter to specify target TCP endpoint
  - Gateway now acts as a client connecting to the specified host:port
  - Automatic reconnection when connection is lost
  - Added `--reconnect-delay` parameter to control retry timing

### Added
- **Connection Management**: 
  - `_maintain_tcp_connection()` method for persistent connection with auto-retry
  - Connection health monitoring with timeout-based detection
  - Graceful handling of connection failures and automatic reconnection
- **Configuration Updates**:
  - Updated `entrypoint.sh` to support `TCP_HOST` environment variable
  - Updated Kubernetes deployment manifests with `TCP_HOST` environment variable
  - Updated Helm chart values and templates for new TCP host configuration
- **Enhanced Documentation**:
  - Updated README.md with new client-mode architecture and usage examples
  - Added TCP endpoint server implementation examples
  - Updated configuration tables and quick start guides

### Technical Details
- Gateway now requires `--tcp-host` parameter to be specified
- Maintains single persistent connection instead of managing multiple client connections
- Connection is established at startup and maintained throughout service lifetime
- UDP messages are dropped if no TCP connection is active (fail-safe behavior)

## [v1.0.3] - 2024-12-19

### Changed
- **Message Protocol**: Implemented length-prefixed protocol to preserve message boundaries
  - UDP datagrams now sent as `[4-byte length][message data]` over TCP
  - Prevents message concatenation in TCP stream
  - Uses big-endian 4-byte unsigned integer for length prefix

### Added
- **Client Helper Function**: Added `read_length_prefixed_message()` utility function
  - Simplifies reading length-prefixed messages for TCP clients
  - Handles proper message boundary detection
  - Includes comprehensive error handling and documentation

- **Message Protocol Documentation**: 
  - Added detailed protocol specification in README.md
  - Provided client implementation examples in Python
  - Documented message format and boundary preservation strategy

### Technical Details
- Message boundaries now guaranteed between UDP datagrams
- TCP clients must read 4-byte length prefix before reading message data
- Helper function available for easy client implementation

## [v1.0.2] - 2024-12-19

### Changed
- **Docker Image References**: Updated all Docker image references from `your-username` to `ericvh`
  - Updated `k8s/deployment.yaml` container image reference
  - Updated `k8s/deployment-with-nodeport.yaml` container image reference
  - Updated `helm/broadcast-gateway/values.yaml` image repository
  - Updated `helm/broadcast-gateway/Chart.yaml` home and sources URLs
  - Updated `README.md` Docker run examples

### Added
- **Development Guidelines** (`DEVELOPMENT.md`):
  - Comprehensive development workflow reminders for git commits
  - Guidelines for maintaining TODO.md, README.md, and CHANGES.md
  - File-specific documentation standards and templates
  - Pre-release checklist and quick reference commands

### Technical Details
- All image references now point to `ghcr.io/ericvh/broadcast-gateway`
- GitHub repository URLs updated to reflect correct username
- Added structured development workflow to ensure consistent documentation maintenance

## [v1.0.1] - 2024-12-19

### Changed
- **Default UDP Port**: Updated default UDP broadcast port from 9999 to 50222 across all configuration files
  - Updated `gateway.py` argument parser default
  - Updated `Dockerfile` environment variable
  - Updated `entrypoint.sh` default value
  - Updated Kubernetes deployment manifests
  - Updated Helm chart values and templates
  - Updated README.md documentation and examples

### Technical Details
- All references to the default UDP port updated consistently across the codebase
- No breaking changes to existing functionality, only default value modification

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

- **Helm Chart** (`helm/broadcast-gateway/`):
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
- **Default Ports**: UDP 50222, TCP 50222
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
