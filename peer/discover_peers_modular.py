#!/usr/bin/env python3
"""
Modular Peer Discovery Tool
Refactored version using separated concerns and clean architecture

This script demonstrates the modular approach to peer discovery with:
- ConnectivityTester: Tests network capabilities
- NetworkScanner: Scans for active peers
- DiscoveryManager: Coordinates the discovery process
"""
import sys
import os
import argparse

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peer.discovery import DiscoveryManager
from peer.config.settings import DISCOVERY_PORT, DEFAULT_SCAN_TIMEOUT


def main():
    """Main function with argument parsing for different discovery modes"""
    parser = argparse.ArgumentParser(
        description="Modular P2P Network Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python discover_peers_modular.py                    # Full discovery
  python discover_peers_modular.py --quick           # Quick peer scan only
  python discover_peers_modular.py --connectivity    # Connectivity test only
  python discover_peers_modular.py --timeout 10      # Custom scan timeout
  python discover_peers_modular.py --quiet          # Minimal output
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                        help='Run quick peer scan only (skip connectivity tests)')
    parser.add_argument('--connectivity', action='store_true',
                        help='Run connectivity tests only (skip peer scanning)')
    parser.add_argument('--timeout', type=int, default=DEFAULT_SCAN_TIMEOUT,
                        help=f'Peer scan timeout in seconds (default: {DEFAULT_SCAN_TIMEOUT})')
    parser.add_argument('--port', type=int, default=DISCOVERY_PORT,
                        help=f'Discovery port (default: {DISCOVERY_PORT})')
    parser.add_argument('--quiet', action='store_true',
                        help='Minimal output mode')
    parser.add_argument('--export', choices=['json', 'summary'],
                        help='Export results in specified format')
    
    args = parser.parse_args()
    
    # Create discovery manager with configured settings
    discovery_manager = DiscoveryManager(
        discovery_port=args.port,
        scan_timeout=args.timeout
    )
    
    verbose = not args.quiet
    
    try:
        # Run appropriate discovery mode
        if args.connectivity:
            results = discovery_manager.test_connectivity_only(verbose)
        elif args.quick:
            results = discovery_manager.quick_peer_scan(verbose)
        else:
            results = discovery_manager.run_full_discovery(verbose)
        
        # Export results if requested
        if args.export:
            exported = discovery_manager.export_results(args.export)
            if args.export == 'json':
                print("\\nExported Results (JSON):")
                print(exported)
            elif args.export == 'summary':
                print("\\nExported Summary:")
                for key, value in exported.items():
                    print(f"  {key}: {value}")
        
        # Return appropriate exit code
        if hasattr(discovery_manager, 'discovery_results'):
            if discovery_manager.discovery_results.get('network_ready', False):
                return 0  # Success
            else:
                return 1  # Network not ready
        else:
            return 0  # Partial operations completed successfully
            
    except KeyboardInterrupt:
        print("\\nDiscovery interrupted by user")
        return 130
    except Exception as e:
        print(f"Error during discovery: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
