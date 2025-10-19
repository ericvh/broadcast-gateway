# TODO List

## Current Tasks

- [ ] Test Docker image build and functionality
- [ ] Validate Kubernetes deployment manifests
- [ ] Test Helm chart installation and configuration
- [ ] Add comprehensive error handling and logging improvements
- [ ] Add monitoring and metrics collection
- [ ] Create integration tests

## Completed Tasks

- [x] Set up basic project documentation structure (README.md, TODO.md, CHANGES.md)
- [x] Implement core UDP to TCP relay gateway service (gateway.py)
- [x] Add iptables firewall rule management for UDP broadcasts
- [x] Create Dockerfile for containerizing the gateway
- [x] Set up GitHub CI/CD pipeline for building Docker images
- [x] Create Kubernetes deployment YAML manifests
- [x] Create Helm chart for easy deployment
- [x] Update comprehensive documentation

## Future Considerations

- Add Prometheus metrics for monitoring
- Implement config file support alongside environment variables
- Add TLS support for TCP connections
- Support for multiple UDP ports
- Add load balancing and high availability features
- Create operator for advanced management
