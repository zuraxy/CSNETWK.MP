#!/usr/bin/env python3
"""
Silent Peer Test
Tests peer discovery with minimal logging
"""
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.core.message_handler import MessageHandler

def test_silent_peer_discovery():
    """Test peer discovery with minimal output"""
    print("Testing peer discovery (silent mode)...")
    
    # Create components
    network_manager = NetworkManager()
    peer_manager = PeerManager()
    peer_manager.set_network_manager(network_manager)
    peer_manager.set_user_id("silent_test")
    
    # Set non-verbose mode
    message_handler = MessageHandler(network_manager, peer_manager, verbose_mode=False)
    
    # Set up quiet peer discovery callback
    peers_found = 0
    def on_peer_discovered(peer_id):
        nonlocal peers_found
        peers_found += 1
        print(f"  Peer found: {peer_id}")
    
    peer_manager.on_peer_discovered = on_peer_discovered
    
    # Start networking
    network_manager.start_listening()
    peer_manager.start_discovery()
    
    print("Running silent discovery test for 15 seconds...")
    print("(Start another instance in a different terminal to test discovery)")
    
    start_time = time.time()
    while time.time() - start_time < 15:
        time.sleep(1)
        if time.time() - start_time >= 5 and peers_found == 0:
            # Show progress every 5 seconds if no peers found
            remaining = 15 - int(time.time() - start_time)
            if remaining % 5 == 0:
                print(f"  Still looking... {remaining}s remaining")
    
    # Cleanup
    peer_manager.stop_discovery()
    network_manager.stop_listening()
    
    print(f"Test complete! Found {peers_found} peers.")
    return peers_found > 0

if __name__ == "__main__":
    test_silent_peer_discovery()
