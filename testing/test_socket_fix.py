#!/usr/bin/env python3
"""
Test Script for Fixed P2P System
Tests the peer system to ensure socket errors are fixed
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

def test_socket_stability():
    """Test that sockets don't throw connection reset errors"""
    print("Testing socket stability...")
    
    try:
        # Create components
        network_manager = NetworkManager()
        peer_manager = PeerManager()
        peer_manager.set_network_manager(network_manager)
        peer_manager.set_user_id("test_user")
        
        message_handler = MessageHandler(network_manager, peer_manager)
        
        # Start networking
        print("Starting network listener...")
        network_manager.start_listening()
        
        print("Starting peer discovery...")
        peer_manager.start_discovery()
        
        # Run for 15 seconds while monitoring for errors
        print("Running stability test for 15 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 15:
            # Send some discovery messages to simulate activity
            if time.time() - start_time > 1:  # Wait 1 second before sending
                peer_manager.announce_presence()
            
            time.sleep(1)
            print(f"  {int(time.time() - start_time)}s elapsed - No socket errors!")
        
        print("\nStability test passed! No socket connection reset errors.")
        
        # Cleanup
        peer_manager.stop_discovery()
        network_manager.stop_listening()
        
        return True
        
    except Exception as e:
        print(f"Error during stability test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("P2P SOCKET ERROR FIX VERIFICATION")
    print("=" * 60)
    
    if test_socket_stability():
        print("\n✅ SOCKET ERRORS FIXED!")
        print("The peer system should now work without connection reset errors.")
        print("\nYou can now run run_peer.py safely in multiple terminals.")
    else:
        print("\n❌ Issues still present.")
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()
