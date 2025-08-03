#!/usr/bin/env python3
"""
Network Scanner Module
Scans for active P2P peers on the network using UDP broadcasts
Follows Single Responsibility Principle - only handles peer scanning
"""
import socket
import time
import sys
import os

# Add parent directories to path for protocol access
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from protocol.protocol import Protocol


class NetworkScanner:
    """
    Handles scanning for P2P peers on the network
    
    Responsibilities:
    - Send discovery broadcasts
    - Listen for peer responses
    - Parse and validate peer information
    - Track discovered peers
    """
    
    def __init__(self, discovery_port=50999, scan_timeout=5.0):
        self.discovery_port = discovery_port
        self.scan_timeout = scan_timeout
        self.scanner_id = 'scanner@127.0.0.1'
        self.discovered_peers = []
        
    def scan_for_peers(self, verbose=True):
        """
        Scan for peers on the network
        
        Returns:
            list: List of discovered peers with their information
        """
        if verbose:
            print("Scanning for P2P peers...")
        
        self.discovered_peers = []
        
        # Create socket for discovery
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2.0)
        
        try:
            # Send discovery broadcasts
            self._send_discovery_broadcasts(sock, verbose)
            
            # Listen for responses
            self._listen_for_responses(sock, verbose)
            
            # Display results
            if verbose:
                self._display_scan_results()
            
        except Exception as e:
            if verbose:
                print(f"Error during scan: {e}")
        finally:
            sock.close()
            
        return self.discovered_peers
    
    def _send_discovery_broadcasts(self, sock, verbose=True):
        """Send discovery broadcasts to find peers"""
        discovery_msg = {
            'TYPE': 'PEER_DISCOVERY',
            'USER_ID': self.scanner_id,
            'PORT': '9999',
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': f'scan{int(time.time())}'
        }
        
        encoded = Protocol.encode_message(discovery_msg)
        
        # Broadcast to different targets
        targets = [
            ('255.255.255.255', self.discovery_port),  # Broadcast
            ('127.0.0.1', self.discovery_port)         # Local
        ]
        
        for target_ip, target_port in targets:
            try:
                sock.sendto(encoded, (target_ip, target_port))
            except Exception as e:
                if verbose:
                    print(f"Failed to send to {target_ip}:{target_port}: {e}")
        
        if verbose:
            print("Discovery broadcast sent, listening for responses...")
    
    def _listen_for_responses(self, sock, verbose=True):
        """Listen for peer discovery responses"""
        start_time = time.time()
        
        while time.time() - start_time < self.scan_timeout:
            try:
                data, addr = sock.recvfrom(65536)
                peer_info = self._parse_peer_response(data, addr)
                
                if peer_info and peer_info not in self.discovered_peers:
                    self.discovered_peers.append(peer_info)
                    if verbose:
                        print(f"Found peer: {peer_info['display_name']}")
                        
            except socket.timeout:
                continue
            except Exception:
                break
    
    def _parse_peer_response(self, data, addr):
        """Parse a peer discovery response"""
        try:
            msg = Protocol.decode_message(data)
            if msg.get('TYPE') == 'PEER_DISCOVERY':
                user_id = msg.get('USER_ID', 'Unknown')
                port = msg.get('PORT', 'Unknown')
                
                # Don't count our own scanner messages
                if user_id != self.scanner_id:
                    return {
                        'user_id': user_id,
                        'ip': addr[0],
                        'port': port,
                        'timestamp': msg.get('TIMESTAMP', ''),
                        'display_name': f"{user_id} at {addr[0]}:{port}"
                    }
        except Exception:
            pass
        
        return None
    
    def _display_scan_results(self):
        """Display scan results in user-friendly format"""
        print(f"\\nScan complete. Found {len(self.discovered_peers)} peers:")
        
        if self.discovered_peers:
            for i, peer in enumerate(self.discovered_peers, 1):
                print(f"  {i}. {peer['display_name']}")
        else:
            print("No peers found. Make sure peers are running and discoverable.")
    
    def get_discovered_peers(self):
        """Get list of discovered peers"""
        return self.discovered_peers
    
    def get_peer_count(self):
        """Get number of discovered peers"""
        return len(self.discovered_peers)
    
    def clear_discovered_peers(self):
        """Clear the discovered peers list"""
        self.discovered_peers = []
    
    def set_scan_timeout(self, timeout):
        """Set the scan timeout in seconds"""
        self.scan_timeout = timeout
    
    def get_scan_summary(self):
        """Get a summary of the last scan"""
        return {
            'peer_count': len(self.discovered_peers),
            'peers': self.discovered_peers,
            'scan_timeout': self.scan_timeout,
            'discovery_port': self.discovery_port
        }
