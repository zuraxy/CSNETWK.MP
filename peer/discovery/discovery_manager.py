#!/usr/bin/env python3
"""
Discovery Manager Module
Coordinates peer discovery operations and integrates connectivity testing with peer scanning
Follows Facade Pattern - provides simplified interface to complex subsystems
"""
import time
from .connectivity_tester import ConnectivityTester
from .network_scanner import NetworkScanner


class DiscoveryManager:
    """
    High-level coordinator for peer discovery operations
    
    Responsibilities:
    - Coordinate connectivity testing and peer scanning
    - Provide simplified interface for discovery operations
    - Generate comprehensive discovery reports
    - Handle discovery workflow orchestration
    """
    
    def __init__(self, discovery_port=50999, scan_timeout=5.0):
        self.connectivity_tester = ConnectivityTester()
        self.network_scanner = NetworkScanner(discovery_port, scan_timeout)
        self.last_discovery_time = None
        self.discovery_results = {}
    
    def run_full_discovery(self, verbose=True):
        """
        Run complete discovery process including connectivity tests and peer scanning
        
        Returns:
            dict: Complete discovery results
        """
        if verbose:
            print("P2P Network Discovery Tool")
            print("=" * 40)
        
        self.last_discovery_time = time.time()
        
        # Step 1: Test connectivity
        connectivity_results = self.connectivity_tester.test_all()
        
        if verbose:
            print()
        
        # Step 2: Scan for peers (only if connectivity is OK)
        if self.connectivity_tester.is_network_ready():
            peer_results = self.network_scanner.scan_for_peers(verbose)
        else:
            if verbose:
                print("Skipping peer scan due to connectivity issues")
            peer_results = []
        
        # Compile results
        self.discovery_results = {
            'connectivity': connectivity_results,
            'peers': peer_results,
            'scan_summary': self.network_scanner.get_scan_summary(),
            'discovery_time': self.last_discovery_time,
            'network_ready': self.connectivity_tester.is_network_ready()
        }
        
        if verbose:
            self._display_final_summary()
        
        return self.discovery_results
    
    def quick_peer_scan(self, verbose=True):
        """Run only peer scanning without connectivity tests"""
        if verbose:
            print("Quick Peer Scan")
            print("-" * 20)
        
        peers = self.network_scanner.scan_for_peers(verbose)
        return {
            'peers': peers,
            'peer_count': len(peers),
            'scan_time': time.time()
        }
    
    def test_connectivity_only(self, verbose=True):
        """Run only connectivity tests without peer scanning"""
        if verbose:
            print("Connectivity Test")
            print("-" * 20)
        
        return self.connectivity_tester.test_all()
    
    def _display_final_summary(self):
        """Display comprehensive discovery summary"""
        print("\\n" + "=" * 50)
        print("DISCOVERY SUMMARY")
        print("=" * 50)
        
        # Connectivity status
        connectivity = self.discovery_results['connectivity']
        print(f"Network Status: {'READY' if self.discovery_results['network_ready'] else 'NOT READY'}")
        print(f"  - Loopback: {connectivity['loopback']['status']}")
        print(f"  - Broadcast: {connectivity['broadcast']['status']}")
        
        # Peer discovery results
        peer_count = len(self.discovery_results['peers'])
        print(f"\\nPeers Discovered: {peer_count}")
        
        if peer_count > 0:
            print("Active Peers:")
            for i, peer in enumerate(self.discovery_results['peers'], 1):
                print(f"  {i}. {peer['display_name']}")
        
        # Next steps
        print("\\n" + "-" * 50)
        if self.discovery_results['network_ready']:
            if peer_count > 0:
                print("✅ Network is ready and peers are available!")
                print("   Ready for P2P communication.")
            else:
                print("✅ Network is ready but no peers found.")
                print("   Start peers with: python run_peer.py")
        else:
            print("❌ Network configuration issues detected.")
            print("   Check firewall and network settings.")
        
        print("\\nTo start a peer: python run_peer.py")
        print("Multiple peers: run the command in separate terminals")
    
    def get_last_results(self):
        """Get the results from the last discovery operation"""
        return self.discovery_results
    
    def get_connectivity_status(self):
        """Get current connectivity status"""
        return self.connectivity_tester.get_last_results()
    
    def get_discovered_peers(self):
        """Get list of discovered peers"""
        return self.network_scanner.get_discovered_peers()
    
    def configure_scan_timeout(self, timeout_seconds):
        """Configure the peer scan timeout"""
        self.network_scanner.set_scan_timeout(timeout_seconds)
    
    def export_results(self, format='dict'):
        """
        Export discovery results in specified format
        
        Args:
            format: 'dict', 'json', or 'summary'
        """
        if format == 'dict':
            return self.discovery_results
        elif format == 'json':
            import json
            return json.dumps(self.discovery_results, indent=2, default=str)
        elif format == 'summary':
            return {
                'network_ready': self.discovery_results.get('network_ready', False),
                'peer_count': len(self.discovery_results.get('peers', [])),
                'discovery_time': self.discovery_results.get('discovery_time'),
                'peers': [peer['display_name'] for peer in self.discovery_results.get('peers', [])]
            }
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def is_ready_for_p2p(self):
        """Check if the system is ready for P2P operations"""
        return (self.discovery_results.get('network_ready', False) and 
                len(self.discovery_results.get('peers', [])) > 0)
