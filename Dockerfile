# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for iptables and networking
RUN apt-get update && apt-get install -y \
    iptables \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
USER root
RUN pip install --no-cache-dir -r requirements.txt

# Copy the gateway application
COPY gateway.py .

# Make the script executable
RUN chmod +x gateway.py

# Create a non-root user for running the application when not using firewall
RUN useradd -m -u 1000 gateway && \
    chown -R gateway:gateway /app

# Expose the TCP port that clients will connect to
EXPOSE 50222

# Default command arguments
ENV UDP_PORT=50222
ENV TCP_PORT=50222
ENV BIND_ADDRESS=0.0.0.0
ENV ENABLE_FIREWALL=false
ENV FIREWALL_INTERFACE=any

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(); s.settimeout(5); s.connect(('localhost', ${TCP_PORT})); s.close()" || exit 1

# Entry point script to handle both root and non-root execution
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default to running the gateway
CMD ["/entrypoint.sh"]
