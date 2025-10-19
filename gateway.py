#!/usr/bin/env python3
"""
Multicast Gateway Service

A service that listens for UDP broadcasts on a specified port and relays them
to connected TCP clients. Includes optional iptables firewall management.
"""

import asyncio
import argparse
import logging
import signal
import sys
import subprocess
import os
from typing import Set, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for the gateway service."""
    udp_port: int
    tcp_port: int
    bind_address: str
    enable_firewall: bool
    firewall_interface: str = "any"


class UDPToTCPGateway:
    """Gateway that forwards UDP broadcasts to TCP clients."""
    
    def __init__(self, config: Config):
        self.config = config
        self.tcp_clients: Set[asyncio.StreamWriter] = set()
        self.udp_transport: Optional[asyncio.DatagramTransport] = None
        self.tcp_server: Optional[asyncio.Server] = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('multicast-gateway')
    
    async def start(self):
        """Start the gateway service."""
        self.logger.info(f"Starting multicast gateway: UDP:{self.config.udp_port} -> TCP:{self.config.tcp_port}")
        
        if self.config.enable_firewall:
            await self._setup_firewall()
        
        # Start TCP server
        self.tcp_server = await asyncio.start_server(
            self._handle_tcp_connection,
            self.config.bind_address,
            self.config.tcp_port
        )
        self.logger.info(f"TCP server listening on {self.config.bind_address}:{self.config.tcp_port}")
        
        # Start UDP listener
        loop = asyncio.get_event_loop()
        self.udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self),
            local_addr=(self.config.bind_address, self.config.udp_port),
            reuse_port=True
        )
        self.logger.info(f"UDP listener started on {self.config.bind_address}:{self.config.udp_port}")
    
    async def stop(self):
        """Stop the gateway service."""
        self.logger.info("Stopping multicast gateway...")
        
        # Close TCP connections
        for writer in self.tcp_clients.copy():
            writer.close()
            await writer.wait_closed()
        
        # Close servers
        if self.tcp_server:
            self.tcp_server.close()
            await self.tcp_server.wait_closed()
        
        if self.udp_transport:
            self.udp_transport.close()
        
        if self.config.enable_firewall:
            await self._cleanup_firewall()
        
        self.logger.info("Gateway stopped")
    
    async def _handle_tcp_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle new TCP client connections."""
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"New TCP client connected: {client_addr}")
        
        self.tcp_clients.add(writer)
        
        try:
            # Keep connection alive and handle any client messages
            while not writer.is_closing():
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if not data:
                        break
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error reading from client {client_addr}: {e}")
                    break
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            self.tcp_clients.discard(writer)
            self.logger.info(f"TCP client disconnected: {client_addr}")
    
    def handle_udp_message(self, data: bytes, addr):
        """Handle incoming UDP broadcast message."""
        if not self.tcp_clients:
            # No clients connected, nothing to do
            return
        
        self.logger.debug(f"UDP message from {addr}: {len(data)} bytes")
        
        # Forward to all connected TCP clients
        disconnected_clients = set()
        for writer in self.tcp_clients:
            try:
                if not writer.is_closing():
                    writer.write(data)
                    # Don't await here to avoid blocking on slow clients
                    asyncio.create_task(self._drain_writer(writer))
                else:
                    disconnected_clients.add(writer)
            except Exception as e:
                self.logger.warning(f"Error forwarding to TCP client: {e}")
                disconnected_clients.add(writer)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            self.tcp_clients.discard(client)
    
    async def _drain_writer(self, writer: asyncio.StreamWriter):
        """Drain a writer and handle any errors."""
        try:
            await writer.drain()
        except Exception as e:
            self.logger.warning(f"Error draining writer: {e}")
    
    async def _setup_firewall(self):
        """Set up iptables rules for UDP broadcasts."""
        if os.geteuid() != 0:
            self.logger.warning("Not running as root, cannot configure iptables")
            return
        
        rules = [
            f"iptables -I INPUT -p udp --dport {self.config.udp_port} -j ACCEPT",
            f"iptables -I FORWARD -p udp --dport {self.config.udp_port} -j ACCEPT"
        ]
        
        if self.config.firewall_interface != "any":
            rules = [
                f"iptables -I INPUT -i {self.config.firewall_interface} -p udp --dport {self.config.udp_port} -j ACCEPT",
                f"iptables -I FORWARD -i {self.config.firewall_interface} -p udp --dport {self.config.udp_port} -j ACCEPT"
            ]
        
        for rule in rules:
            try:
                result = subprocess.run(rule.split(), check=True, capture_output=True, text=True)
                self.logger.info(f"Added firewall rule: {rule}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to add firewall rule '{rule}': {e}")
    
    async def _cleanup_firewall(self):
        """Remove iptables rules."""
        if os.geteuid() != 0:
            self.logger.warning("Not running as root, cannot clean up iptables")
            return
        
        rules = [
            f"iptables -D INPUT -p udp --dport {self.config.udp_port} -j ACCEPT",
            f"iptables -D FORWARD -p udp --dport {self.config.udp_port} -j ACCEPT"
        ]
        
        if self.config.firewall_interface != "any":
            rules = [
                f"iptables -D INPUT -i {self.config.firewall_interface} -p udp --dport {self.config.udp_port} -j ACCEPT",
                f"iptables -D FORWARD -i {self.config.firewall_interface} -p udp --dport {self.config.udp_port} -j ACCEPT"
            ]
        
        for rule in rules:
            try:
                result = subprocess.run(rule.split(), check=True, capture_output=True, text=True)
                self.logger.info(f"Removed firewall rule: {rule}")
            except subprocess.CalledProcessError as e:
                # Rule might not exist, that's okay
                self.logger.debug(f"Could not remove firewall rule '{rule}': {e}")


class UDPProtocol:
    """Protocol class for handling UDP datagrams."""
    
    def __init__(self, gateway: UDPToTCPGateway):
        self.gateway = gateway
    
    def datagram_received(self, data: bytes, addr):
        """Called when a UDP datagram is received."""
        self.gateway.handle_udp_message(data, addr)
    
    def error_received(self, exc):
        """Called when a UDP error occurs."""
        self.gateway.logger.error(f"UDP error: {exc}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='UDP to TCP Multicast Gateway')
    parser.add_argument('--udp-port', type=int, default=50222, help='UDP port to listen on')
    parser.add_argument('--tcp-port', type=int, default=8888, help='TCP port to serve on')
    parser.add_argument('--bind-address', default='0.0.0.0', help='Address to bind to')
    parser.add_argument('--enable-firewall', action='store_true', help='Enable iptables firewall rules')
    parser.add_argument('--firewall-interface', default='any', help='Network interface for firewall rules')
    
    args = parser.parse_args()
    
    config = Config(
        udp_port=args.udp_port,
        tcp_port=args.tcp_port,
        bind_address=args.bind_address,
        enable_firewall=args.enable_firewall,
        firewall_interface=args.firewall_interface
    )
    
    gateway = UDPToTCPGateway(config)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(gateway.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await gateway.start()
        
        # Keep the service running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await gateway.stop()


if __name__ == '__main__':
    asyncio.run(main())
