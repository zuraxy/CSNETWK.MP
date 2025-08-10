#!/usr/bin/env python3
"""
Simple P2P Discovery Test
Tests the peer discovery functionality in isolation
"""
import sys
import os
import time
import threading

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.core.message_handler import MessageHandler

def test_peer_discovery():
    """Test basic peer discovery functionality"""
    print("=" * 60)
    print("P2P DISCOVERY TEST")
    print("=" * 60)
    
    # Get a unique user ID for this test instance
    import random
    user_id = f"test_user_{random.randint(1000, 9999)}"
    
    print(f"Starting test as: {user_id}")
    
    try:
        # Initialize components
        print("\n1. Initializing network manager...")
        network_manager = NetworkManager()
        print(f"   Network info: {network_manager.get_network_info()}")
        
        print("\n2. Initializing peer manager...")
        peer_manager = PeerManager()
        peer_manager.set_network_manager(network_manager)
        peer_manager.set_user_id(user_id)
        
        # Set up peer discovery callback
        def on_peer_discovered(peer_id):
            print(f"   *** NEW PEER DISCOVERED: {peer_id} ***")
        
        peer_manager.on_peer_discovered = on_peer_discovered
        
        print("\n3. Initializing message handler...")
        message_handler = MessageHandler(network_manager, peer_manager, verbose_mode=True)
        
        print("\n4. Starting network listener...")
        network_manager.start_listening()
        
        print("\n5. Starting peer discovery...")
        peer_manager.start_discovery()
        
        print(f"\n6. Running discovery test for 30 seconds...")
        print(f"   User ID: {user_id}")
        print(f"   Local IP: {network_manager.local_ip}")
        print(f"   Local Port: {network_manager.local_port}")
        print(f"   Discovery Port: {network_manager.discovery_port}")
        print(f"   Has Discovery Socket: {network_manager.has_discovery_socket}")
        
        # Monitor for 30 seconds
        start_time = time.time()
        last_peer_check = 0
        
        while time.time() - start_time < 30:
            current_time = time.time() - start_time
            
            # Show peer count every 5 seconds
            if current_time - last_peer_check >= 5:
                peer_list = peer_manager.get_peer_list()
                print(f"\n   [{int(current_time)}s] Known peers: {len(peer_list)}")
                if peer_list:
                    for peer_id in peer_list:
                        peer_info = peer_manager.get_peer_info(peer_id)
                        print(f"     - {peer_id} at {peer_info['ip']}:{peer_info['port']}")
                last_peer_check = current_time
            
            time.sleep(1)
        
        print(f"\n7. Test completed!")
        final_peer_list = peer_manager.get_peer_list()
        print(f"   Final peer count: {len(final_peer_list)}")
        if final_peer_list:
            print("   Discovered peers:")
            for peer_id in final_peer_list:
                peer_info = peer_manager.get_peer_info(peer_id)
                print(f"     - {peer_id} at {peer_info['ip']}:{peer_info['port']}")
        else:
            print("   No peers discovered")
        
        print("\n8. Cleaning up...")
        peer_manager.stop_discovery()
        network_manager.stop_listening()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_peer_discovery()
