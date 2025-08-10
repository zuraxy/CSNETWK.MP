#!/usr/bin/env python3
"""
Quick Peer Discovery Diagnostic
Run this in multiple terminal windows to test peer discovery
"""
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_network():
    """Test basic network functionality"""
    print("Testing basic network functionality...")
    
    # Test 1: Check if we can create UDP sockets
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print("✓ UDP socket creation: OK")
        sock.close()
    except Exception as e:
        print(f"✗ UDP socket creation: FAILED - {e}")
        return False
    
    # Test 2: Check port availability
    try:
        from peer.config.settings import DISCOVERY_PORT
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        print(f"✓ Discovery port {DISCOVERY_PORT}: Available")
        sock.close()
    except Exception as e:
        print(f"✗ Discovery port {DISCOVERY_PORT}: In use or blocked - {e}")
        # Try alternative port
        try:
            alt_port = DISCOVERY_PORT + 1
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', alt_port))
            print(f"✓ Alternative port {alt_port}: Available")
            sock.close()
        except Exception as e2:
            print(f"✗ Alternative port {alt_port}: Also blocked - {e2}")
    
    # Test 3: Test local IP detection
    try:
        from peer.network.network_manager import NetworkManager
        nm = NetworkManager()
        local_ip = nm._get_local_ip()
        print(f"✓ Local IP detection: {local_ip}")
    except Exception as e:
        print(f"✗ Local IP detection: FAILED - {e}")
    
    return True

def test_simple_discovery():
    """Run a simple peer discovery test"""
    print("\nStarting simple peer discovery test...")
    
    try:
        from peer.network.network_manager import NetworkManager
        from peer.discovery.peer_manager import PeerManager
        from peer.core.message_handler import MessageHandler
        
        # Create a unique user ID
        import random
        user_id = f"test_{random.randint(100, 999)}"
        print(f"User ID: {user_id}")
        
        # Initialize components
        network_manager = NetworkManager()
        peer_manager = PeerManager()
        peer_manager.set_network_manager(network_manager)
        peer_manager.set_user_id(user_id)
        
        message_handler = MessageHandler(network_manager, peer_manager)
        
        # Display network info
        net_info = network_manager.get_network_info()
        print(f"Local IP: {net_info['local_ip']}")
        print(f"Local Port: {net_info['local_port']}")
        print(f"Discovery Port: {net_info['discovery_port']}")
        print(f"Has Discovery Socket: {net_info['has_discovery_socket']}")
        
        # Start networking
        network_manager.start_listening()
        peer_manager.start_discovery()
        
        print("\nListening for peers for 15 seconds...")
        print("If you have other instances running, they should be discovered now.")
        
        for i in range(15):
            peer_count = len(peer_manager.get_peer_list())
            print(f"  {15-i:2d}s remaining - Peers found: {peer_count}", end="\\r")
            time.sleep(1)
        
        # Show results
        print("\\n\\nDiscovery complete!")
        peer_list = peer_manager.get_peer_list()
        if peer_list:
            print(f"Found {len(peer_list)} peers:")
            for peer_id in peer_list:
                peer_info = peer_manager.get_peer_info(peer_id)
                print(f"  - {peer_id} at {peer_info['ip']}:{peer_info['port']}")
        else:
            print("No peers found.")
            print("Try running this script in another terminal window/CLI.")
        
        # Cleanup
        peer_manager.stop_discovery()
        network_manager.stop_listening()
        
    except Exception as e:
        print(f"Error during discovery test: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 50)
    print("PEER DISCOVERY DIAGNOSTIC")
    print("=" * 50)
    
    if test_basic_network():
        test_simple_discovery()
    
    print("\\nDiagnostic complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
