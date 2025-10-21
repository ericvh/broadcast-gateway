#!/usr/bin/env python3
"""
Broadcast Gateway Service

A service that listens for UDP broadcasts on a specified port and forwards them
to a connected TCP endpoint. Includes optional iptables firewall management and
automatic reconnection capabilities.

Message Protocol:
TCP endpoint receives messages in the following format:
[4-byte length in big-endian format][message data]

This preserves message boundaries from UDP datagrams in the TCP stream.
"""

import asyncio
import argparse
import logging
import signal
import sys
import subprocess
import os
import struct
from typing import Set, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for the gateway service."""
    udp_port: int
    tcp_host: str
    tcp_port: int
    bind_address: str
    enable_firewall: bool
    firewall_interface: str = "any"
    reconnect_delay: float = 5.0


class UDPToTCPGateway:
    """Gateway that forwards UDP broadcasts to a connected TCP endpoint."""
    
    def __init__(self, config: Config):
        self.config = config
        self.tcp_writer: Optional[asyncio.StreamWriter] = None
        self.tcp_reader: Optional[asyncio.StreamReader] = None
        self.udp_transport: Optional[asyncio.DatagramTransport] = None
        self.logger = self._setup_logging()
        self._connection_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('broadcast-gateway')
    
    async def start(self):
        """Start the gateway service."""
        self.logger.info(f"Starting broadcast gateway: UDP:{self.config.udp_port} -> TCP:{self.config.tcp_host}:{self.config.tcp_port}")
        
        if self.config.enable_firewall:
            await self._setup_firewall()
        
        # Start UDP listener first
        loop = asyncio.get_event_loop()
        self.udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self),
            local_addr=(self.config.bind_address, self.config.udp_port),
            reuse_port=True
        )
        self.logger.info(f"UDP listener started on {self.config.bind_address}:{self.config.udp_port}")
        
        # Start connection to TCP endpoint
        self._connection_task = asyncio.create_task(self._maintain_tcp_connection())
    
    async def stop(self):
        """Stop the gateway service."""
        self.logger.info("Stopping broadcast gateway...")
        self._shutdown = True
        
        # Cancel connection task
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
        
        # Close TCP connection
        if self.tcp_writer and not self.tcp_writer.is_closing():
            self.tcp_writer.close()
            try:
                await self.tcp_writer.wait_closed()
            except Exception:
                pass
        
        # Close UDP transport
        if self.udp_transport:
            self.udp_transport.close()
        
        if self.config.enable_firewall:
            await self._cleanup_firewall()
        
        self.logger.info("Gateway stopped")
    
    async def _maintain_tcp_connection(self):
        """Maintain connection to the TCP endpoint with auto-reconnect."""
        while not self._shutdown:
            try:
                self.logger.info(f"Connecting to TCP endpoint: {self.config.tcp_host}:{self.config.tcp_port}")
                self.tcp_reader, self.tcp_writer = await asyncio.open_connection(
                    self.config.tcp_host, 
                    self.config.tcp_port
                )
                self.logger.info(f"Connected to TCP endpoint: {self.config.tcp_host}:{self.config.tcp_port}")
                
                # Monitor connection health by reading any incoming data
                try:
                    while not self.tcp_writer.is_closing() and not self._shutdown:
                        await asyncio.wait_for(self.tcp_reader.read(1024), timeout=10.0)
                except asyncio.TimeoutError:
                    # No data received in 10 seconds - connection is still alive
                    continue
                except Exception as e:
                    self.logger.warning(f"TCP connection error: {e}")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Failed to connect to TCP endpoint {self.config.tcp_host}:{self.config.tcp_port}: {e}")
            
            # Clean up current connection
            if self.tcp_writer and not self.tcp_writer.is_closing():
                self.tcp_writer.close()
                try:
                    await self.tcp_writer.wait_closed()
                except Exception:
                    pass
            
            self.tcp_reader = None
            self.tcp_writer = None
            
            if not self._shutdown:
                self.logger.info(f"Retrying connection in {self.config.reconnect_delay} seconds...")
                await asyncio.sleep(self.config.reconnect_delay)
    
    def handle_udp_message(self, data: bytes, addr):
        """Handle incoming UDP broadcast message."""
        if not self.tcp_writer or self.tcp_writer.is_closing():
            # No TCP connection active, skip message
            self.logger.debug(f"UDP message from {addr} dropped - no TCP connection")
            return
        
        self.logger.debug(f"UDP message from {addr}: {len(data)} bytes")
        
        # Create message with length prefix to preserve boundaries
        # Format: [4-byte length][message data]
        message_length = len(data)
        length_prefix = struct.pack('>I', message_length)  # Big-endian 4-byte unsigned int
        message_with_boundary = length_prefix + data
        
        # Forward to TCP endpoint
        try:
            self.tcp_writer.write(message_with_boundary)
            asyncio.create_task(self._drain_writer(self.tcp_writer))
        except Exception as e:
            self.logger.warning(f"Error forwarding UDP message to TCP endpoint: {e}")
    
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


async def read_length_prefixed_message(reader: asyncio.StreamReader) -> Optional[bytes]:
    """
    Helper function for TCP clients to read length-prefixed messages.
    
    Args:
        reader: The asyncio StreamReader connected to the gateway
        
    Returns:
        The message data bytes, or None if connection is closed
        
    Raises:
        asyncio.IncompleteReadError: If the connection is closed unexpectedly
        struct.error: If the length prefix is invalid
    """
    # Read the 4-byte length prefix
    length_data = await reader.readexactly(4)
    if not length_data:
        return None
    
    # Unpack the length (big-endian 4-byte unsigned int)
    message_length = struct.unpack('>I', length_data)[0]
    
    # Read the message data
    message_data = await reader.readexactly(message_length)
    
    return message_data


class UDPProtocol(asyncio.DatagramProtocol):
    """Protocol class for handling UDP datagrams."""
    
    def __init__(self, gateway: UDPToTCPGateway):
        self.gateway = gateway
    
    def connection_made(self, transport):
        """Called when a connection is made."""
        self.gateway.logger.debug("UDP connection made")
    
    def connection_lost(self, exc):
        """Called when the connection is lost or closed."""
        self.gateway.logger.debug(f"UDP connection lost: {exc}")
    
    def datagram_received(self, data: bytes, addr):
        """Called when a UDP datagram is received."""
        self.gateway.handle_udp_message(data, addr)
    
    def error_received(self, exc):
        """Called when a UDP error occurs."""
        self.gateway.logger.error(f"UDP error: {exc}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='UDP to TCP Broadcast Gateway')
    parser.add_argument('--udp-port', type=int, default=50222, help='UDP port to listen on')
    parser.add_argument('--tcp-host', required=True, help='TCP host to connect to')
    parser.add_argument('--tcp-port', type=int, default=8888, help='TCP port to connect to')
    parser.add_argument('--bind-address', default='0.0.0.0', help='Address to bind UDP listener to')
    parser.add_argument('--enable-firewall', action='store_true', help='Enable iptables firewall rules')
    parser.add_argument('--firewall-interface', default='any', help='Network interface for firewall rules')
    parser.add_argument('--reconnect-delay', type=float, default=5.0, help='Delay between reconnection attempts (seconds)')
    
    args = parser.parse_args()
    
    config = Config(
        udp_port=args.udp_port,
        tcp_host=args.tcp_host,
        tcp_port=args.tcp_port,
        bind_address=args.bind_address,
        enable_firewall=args.enable_firewall,
        firewall_interface=args.firewall_interface,
        reconnect_delay=args.reconnect_delay
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
