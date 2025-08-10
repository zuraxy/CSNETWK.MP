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
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
        
        # Windows-specific socket options to handle connection resets gracefully
        if hasattr(socket, 'SIO_UDP_CONNRESET'):
            # Disable UDP connection reset errors on Windows
            try:
                self.socket.ioctl(socket.SIO_UDP_CONNRESET, 0)
            except AttributeError:
                pass  # Not available on all Python versions
        
        # Try to bind to a free port
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                self.socket.bind(("", self.local_port))
                break
            except OSError:
                self.local_port = random.randint(*peer_port_range)
                if attempt == max_attempts - 1:
                    raise Exception(f"Could not bind to any port in range {peer_port_range}")
        
        print(f"Main socket bound to port {self.local_port}")
        
        # Discovery socket for peer announcements - simplified approach
        # For Windows compatibility, we'll use a separate socket only if binding succeeds
        self.discovery_socket = None
        self.has_discovery_socket = False
        
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Windows-specific socket options for discovery socket too
            if hasattr(socket, 'SIO_UDP_CONNRESET'):
                try:
                    self.discovery_socket.ioctl(socket.SIO_UDP_CONNRESET, 0)
                except AttributeError:
                    pass
            
            self.discovery_socket.bind(("", discovery_port))
            self.has_discovery_socket = True
        except Exception:
            if self.discovery_socket:
                self.discovery_socket.close()
                self.discovery_socket = None
        
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
        
        # Start discovery listener only if we have a separate discovery socket
        if self.has_discovery_socket and self.discovery_socket:
            discovery_thread = threading.Thread(target=self._listen_discovery_socket)
            discovery_thread.daemon = True
            discovery_thread.start()
    
    def stop_listening(self):
        """Stop listening for messages"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        if self.has_discovery_socket and self.discovery_socket:
            try:
                self.discovery_socket.close()
            except:
                pass
    
    def _listen_main_socket(self):
        """Listen for messages on main socket"""
        while self.running:
            try:
                # Set a timeout to prevent indefinite blocking
                self.socket.settimeout(1.0)
                data, addr = self.socket.recvfrom(SOCKET_BUFFER_SIZE)
                self._handle_message(data, addr)
            except socket.timeout:
                # Timeout is normal, just continue
                continue
            except ConnectionResetError:
                # Windows-specific error: ignore connection resets on UDP
                continue
            except OSError as e:
                # Handle Windows error 10054 and similar UDP errors
                if e.winerror == 10054 or "forcibly closed" in str(e):
                    # Connection reset by peer - normal for UDP, just continue
                    continue
                elif self.running:
                    print(f"Socket error on main socket: {e}")
                    break
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Error receiving message on main socket: {e}")
                    # Don't break on single errors, just continue
                    continue
    
    def _listen_discovery_socket(self):
        """Listen for discovery messages"""
        while self.running:
            try:
                # Set a timeout to prevent indefinite blocking
                self.discovery_socket.settimeout(1.0)
                data, addr = self.discovery_socket.recvfrom(SOCKET_BUFFER_SIZE)
                self._handle_message(data, addr)
            except socket.timeout:
                # Timeout is normal, just continue
                continue
            except ConnectionResetError:
                # Windows-specific error: ignore connection resets on UDP
                continue
            except OSError as e:
                # Handle Windows error 10054 and similar UDP errors
                if e.winerror == 10054 or "forcibly closed" in str(e):
                    # Connection reset by peer - normal for UDP, just continue
                    continue
                elif self.running:
                    print(f"Socket error on discovery socket: {e}")
                    break
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Error receiving discovery message: {e}")
                    # Don't break on single errors, just continue
                    continue
    
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
            sent_count = 0
            
            # Use main socket to send to discovery port and peer ports
            for address in BROADCAST_ADDRESSES:
                try:
                    # Send to discovery port
                    self.socket.sendto(encoded_data, (address, self.discovery_port))
                    sent_count += 1
                    
                    # Also send to a range of peer ports to catch other instances
                    for port in range(self.peer_port_range[0], min(self.peer_port_range[0] + 20, self.peer_port_range[1])):
                        try:
                            self.socket.sendto(encoded_data, (address, port))
                        except:
                            pass  # Ignore failures for port scanning
                            
                except Exception:
                    pass  # Silently ignore broadcast failures
            
            # Direct localhost attempts
            try:
                self.socket.sendto(encoded_data, ('127.0.0.1', self.discovery_port))
                sent_count += 1
            except Exception:
                pass  # Silently ignore localhost failures
                
            return sent_count > 0
        except Exception:
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