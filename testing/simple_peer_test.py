#!/usr/bin/env python3
"""
Simple Dual Peer Test
Start this script, then run it again in another terminal.
The two instances should discover each other.
"""
import sys
import os
import time
import random

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.core.message_handler import MessageHandler

def main():
    # Create unique user ID
    user_id = f"peer_{random.randint(100, 999)}"
    
    print("=" * 50)
    print(f"PEER DISCOVERY TEST - {user_id}")
    print("=" * 50)
    
    try:
        # Initialize P2P components
        print("Initializing P2P system...")
        network_manager = NetworkManager()
        peer_manager = PeerManager()
        peer_manager.set_network_manager(network_manager)
        peer_manager.set_user_id(user_id)
        
        # Set up callbacks
        def on_peer_discovered(peer_id):
            print(f"\n*** PEER DISCOVERED: {peer_id} ***")
            peer_info = peer_manager.get_peer_info(peer_id)
            print(f"    Address: {peer_info['ip']}:{peer_info['port']}")
        
        peer_manager.on_peer_discovered = on_peer_discovered
        
        # Initialize message handler
        message_handler = MessageHandler(network_manager, peer_manager)
        
        # Show configuration
        net_info = network_manager.get_network_info()
        print(f"User ID: {user_id}")
        print(f"Local Port: {net_info['local_port']}")
        print(f"Discovery Port: {net_info['discovery_port']}")
        print(f"Has Discovery Socket: {net_info['has_discovery_socket']}")
        
        # Start networking
        print("\\nStarting network listeners...")
        network_manager.start_listening()
        
        print("Starting peer discovery...")
        peer_manager.start_discovery()
        
        print("\\nRunning for 30 seconds. Start another instance now!")
        print("Press Ctrl+C to stop early.")
        
        # Run for 30 seconds
        try:
            for i in range(30):
                time.sleep(1)
                peer_count = len(peer_manager.get_peer_list())
                if i % 5 == 4:  # Every 5 seconds
                    print(f"\\n[{i+1}s] Current peers: {peer_count}")
                    if peer_count > 0:
                        for peer_id in peer_manager.get_peer_list():
                            peer_info = peer_manager.get_peer_info(peer_id)
                            print(f"  - {peer_id} at {peer_info['ip']}:{peer_info['port']}")
        except KeyboardInterrupt:
            print("\\nStopping early...")
        
        # Final results
        final_peers = peer_manager.get_peer_list()
        print(f"\\nFinal Results:")
        print(f"Peers discovered: {len(final_peers)}")
        for peer_id in final_peers:
            peer_info = peer_manager.get_peer_info(peer_id)
            print(f"  - {peer_id} at {peer_info['ip']}:{peer_info['port']}")
        
        # Cleanup
        print("\\nCleaning up...")
        peer_manager.stop_discovery()
        network_manager.stop_listening()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("Test complete!")

if __name__ == "__main__":
    main()
