# Test imports functionality
# This script tests that all necessary imports work correctly from the testing directory

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all_imports():
    """Test that all necessary modules can be imported from testing directory"""
    print("Testing imports from testing directory...")
    
    try:
        from protocol.protocol import Protocol
        print("Protocol import successful")
    except ImportError as e:
        print(f"Protocol import failed: {e}")
        return False
    
    try:
        from peer.udp_peer_modular import UDPPeerModular
        print("Peer import successful")
    except ImportError as e:
        print(f"Peer import failed: {e}")
        return False
    
    print("All imports successful!")
    return True

if __name__ == "__main__":
    test_all_imports()
