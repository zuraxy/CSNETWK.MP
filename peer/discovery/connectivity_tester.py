#!/usr/bin/env python3
"""
Connectivity Tester Module
Tests basic UDP connectivity, loopback, and broadcast capabilities
Follows Single Responsibility Principle - only tests connectivity
"""
import socket
import time


class ConnectivityTester:
    """
    Handles testing network connectivity capabilities
    
    Responsibilities:
    - Test local UDP loopback
    - Test broadcast capabilities
    - Validate network configuration
    """
    
    def __init__(self):
        self.results = {}
    
    def test_all(self):
        """Run all connectivity tests and return results"""
        print("Testing UDP connectivity...")
        
        self.results = {
            'loopback': self._test_loopback(),
            'broadcast': self._test_broadcast(),
            'timestamp': time.time()
        }
        
        self._display_results()
        return self.results
    
    def _test_loopback(self):
        """Test local UDP loopback connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('127.0.0.1', 0))
            local_port = sock.getsockname()[1]
            
            # Send test message to ourselves
            test_msg = b"UDP_TEST"
            sock.sendto(test_msg, ('127.0.0.1', local_port))
            sock.settimeout(1.0)
            
            data, addr = sock.recvfrom(1024)
            sock.close()
            
            return {
                'status': 'OK' if data == test_msg else 'FAILED',
                'details': 'Local UDP messaging working correctly' if data == test_msg else 'Message mismatch',
                'port': local_port
            }
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'details': str(e),
                'port': None
            }
    
    def _test_broadcast(self):
        """Test UDP broadcast capability"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(b"BROADCAST_TEST", ('255.255.255.255', 50999))
            sock.close()
            
            return {
                'status': 'OK',
                'details': 'Broadcast capability available',
                'target': '255.255.255.255:50999'
            }
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'details': str(e),
                'target': '255.255.255.255:50999'
            }
    
    def _display_results(self):
        """Display test results in user-friendly format"""
        print(f"Local UDP connectivity: {self.results['loopback']['status']}")
        if self.results['loopback']['status'] != 'OK':
            print(f"  Details: {self.results['loopback']['details']}")
        
        print(f"Broadcast capability: {self.results['broadcast']['status']}")
        if self.results['broadcast']['status'] != 'OK':
            print(f"  Details: {self.results['broadcast']['details']}")
    
    def get_last_results(self):
        """Get the most recent test results"""
        return self.results
    
    def is_network_ready(self):
        """Check if network is ready for P2P operations"""
        if not self.results:
            return False
        
        return (self.results['loopback']['status'] == 'OK' and 
                self.results['broadcast']['status'] == 'OK')
