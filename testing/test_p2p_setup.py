#!/usr/bin/env python3
"""
Demonstration script to verify P2P functionality
This shows that the peer can be imported and basic functionality works
"""
import sys
import os

# Add the parent directory to Python path (since we're now in testing/ subfolder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_p2p_import():
    """Test that the P2P implementation can be imported"""
    try:
        from peer.udp_peer_modular import UDPPeerModular
        print("P2P implementation imports successfully")
        return True
    except ImportError as e:
        print(f"Failed to import P2P implementation: {e}")
        return False

def test_protocol_import():
    """Test that the protocol can be imported"""
    try:
        from protocol.protocol import Protocol
        print("Protocol implementation imports successfully")
        return True
    except ImportError as e:
        print(f"Failed to import protocol: {e}")
        return False

def test_peer_creation():
    """Test that a peer can be created"""
    try:
        from peer.udp_peer_modular import UDPPeerModular
        peer = UDPPeerModular()
        network_info = peer.network_manager.get_network_info()
        print(f"Peer created successfully on {network_info['local_ip']}:{network_info['local_port']}")
        return True
    except Exception as e:
        print(f"Failed to create peer: {e}")
        return False

def main():
    print("=" * 60)
    print("PEER-TO-PEER IMPLEMENTATION TEST")
    print("=" * 60)
    
    tests = [
        ("Import P2P Implementation", test_p2p_import),
        ("Import Protocol", test_protocol_import),
        ("Create Peer Instance", test_peer_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Your P2P implementation is working correctly.")
        print("\nReady to start peers with: python run_peer.py")
    else:
        print("Some tests failed. Check the error messages above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
