#!/usr/bin/env python3
"""
Network Layer Module
Handles all network communication including UDP sockets, broadcasting, and peer connections
"""
import socket
import threading
import random
import time
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from protocol.protocol import Protocol
from peer.config.settings import (
    DISCOVERY_PORT, 
    PEER_PORT_RANGE,
    SOCKET_BUFFER_SIZE,
    BROADCAST_ADDRESSES
)

class NetworkManager:
    """Manages all network communication for P2P peers"""
    
    def __init__(self, discovery_port=DISCOVERY_PORT, peer_port_range=PEER_PORT_RANGE):
        self.discovery_port = discovery_port
        self.peer_port_range = peer_port_range
        
        # Network configuration
        self.local_port = random.randint(*peer_port_range)
        self.local_ip = self._get_local_ip()
        
        # Main communication socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind(("", self.local_port))
        
        # Discovery socket for peer announcements
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.discovery_socket.bind(("", discovery_port))
            self.has_discovery_socket = True
            print(f"Discovery socket bound to port {discovery_port}")
        except Exception as e:
            print(f"Warning: Could not bind discovery socket to port {discovery_port}: {e}")
            self.has_discovery_socket = False
        
        # Message handlers registry
        self.message_handlers = {}
        self.running = False
        
    def _get_local_ip(self):
        """Get the local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def register_message_handler(self, message_type, handler_func):
        """Register a handler function for a specific message type"""
        self.message_handlers[message_type] = handler_func
    
    def start_listening(self):
        """Start listening for incoming messages"""
        self.running = True
        
        # Start main message listener
        main_thread = threading.Thread(target=self._listen_main_socket)
        main_thread.daemon = True
        main_thread.start()
        
        # Start discovery listener if available
        if self.has_discovery_socket:
            discovery_thread = threading.Thread(target=self._listen_discovery_socket)
            discovery_thread.daemon = True
            discovery_thread.start()
    
    def stop_listening(self):
        """Stop listening for messages"""
        self.running = False
        self.socket.close()
        if self.has_discovery_socket:
            self.discovery_socket.close()
    
    def _listen_main_socket(self):
        """Listen for messages on main socket"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(SOCKET_BUFFER_SIZE)
                self._handle_message(data, addr)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Error receiving message on main socket: {e}")
    
    def _listen_discovery_socket(self):
        """Listen for discovery messages"""
        while self.running:
            try:
                data, addr = self.discovery_socket.recvfrom(SOCKET_BUFFER_SIZE)
                self._handle_message(data, addr)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Error receiving discovery message: {e}")
    
    def _handle_message(self, data, addr):
        """Process incoming messages and route to appropriate handlers"""
        try:
            msg_dict = Protocol.decode_message(data)
            msg_type = msg_dict.get('TYPE', '')
            
            if msg_type in self.message_handlers:
                self.message_handlers[msg_type](msg_dict, addr)
            else:
                print(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            print(f"Error processing message from {addr}: {e}")
    
    def send_to_address(self, data, ip, port):
        """Send data to a specific address"""
        try:
            if isinstance(data, dict):
                encoded_data = Protocol.encode_message(data)
            else:
                encoded_data = data
            
            self.socket.sendto(encoded_data, (ip, port))
            return True
        except Exception as e:
            print(f"Error sending to {ip}:{port}: {e}")
            return False
    
    def broadcast_discovery(self, message):
        """Broadcast a discovery message"""
        try:
            encoded_data = Protocol.encode_message(message)
            # Broadcast to local network using configured addresses
            for address in BROADCAST_ADDRESSES:
                self.socket.sendto(encoded_data, (address, self.discovery_port))
            return True
        except Exception as e:
            print(f"Error broadcasting discovery: {e}")
            return False
    
    def broadcast_to_peers(self, data, peer_list):
        """Send data to all peers in the list"""
        sent_count = 0
        for peer_info in peer_list.values():
            if self.send_to_address(data, peer_info['ip'], peer_info['port']):
                sent_count += 1
        return sent_count
    
    def get_network_info(self):
        """Get network configuration information"""
        return {
            'local_ip': self.local_ip,
            'local_port': self.local_port,
            'discovery_port': self.discovery_port,
            'has_discovery_socket': self.has_discovery_socket
        }