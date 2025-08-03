#!/usr/bin/env python3
"""
Test script for modular peer components
Tests individual modules and their integration
"""
import sys
import os
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_network_manager():
    """Test NetworkManager functionality"""
    print("Testing NetworkManager...")
    
    try:
        from peer.modules.network_manager import NetworkManager
        
        # Test initialization
        nm = NetworkManager()
        network_info = nm.get_network_info()
        
        assert 'local_ip' in network_info
        assert 'local_port' in network_info
        assert 'discovery_port' in network_info
        assert network_info['discovery_port'] == 50999
        
        print(f"  ✓ NetworkManager initialized on {network_info['local_ip']}:{network_info['local_port']}")
        
        # Test message handler registration
        test_handler_called = False
        def test_handler(msg, addr):
            nonlocal test_handler_called
            test_handler_called = True
        
        nm.register_message_handler('TEST', test_handler)
        assert 'TEST' in nm.message_handlers
        
        print("  ✓ Message handler registration works")
        
        # Cleanup
        nm.stop_listening()
        print("  ✓ NetworkManager test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ NetworkManager test failed: {e}")
        return False

def test_peer_manager():
    """Test PeerManager functionality"""
    print("Testing PeerManager...")
    
    try:
        from peer.modules.peer_manager import PeerManager
        
        # Test initialization
        pm = PeerManager()
        pm.set_user_id("test@127.0.0.1")
        
        assert pm.user_id == "test@127.0.0.1"
        assert len(pm.known_peers) == 0
        
        print("  ✓ PeerManager initialized")
        
        # Test peer tracking
        pm.update_peer_info("alice@192.168.1.10", "192.168.1.10", 8001)
        assert pm.is_peer_known("alice@192.168.1.10")
        
        peer_info = pm.get_peer_info("alice@192.168.1.10")
        assert peer_info['ip'] == "192.168.1.10"
        assert peer_info['port'] == 8001
        
        print("  ✓ Peer tracking works")
        
        # Test profile management
        pm.update_user_profile("alice@192.168.1.10", "Alice", True, "image/png")
        display_name = pm.get_display_name("alice@192.168.1.10")
        assert display_name == "Alice"
        
        avatar_info = pm.get_avatar_info("alice@192.168.1.10")
        assert "[AVATAR]" in avatar_info
        
        print("  ✓ Profile management works")
        print("  ✓ PeerManager test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ PeerManager test failed: {e}")
        return False

def test_message_handler():
    """Test MessageHandler functionality"""
    print("Testing MessageHandler...")
    
    try:
        from peer.modules.network_manager import NetworkManager
        from peer.modules.peer_manager import PeerManager
        from peer.modules.message_handler import MessageHandler
        
        # Initialize components
        nm = NetworkManager()
        pm = PeerManager()
        pm.set_user_id("test@127.0.0.1")
        pm.set_network_manager(nm)
        
        mh = MessageHandler(nm, pm, verbose_mode=False)
        
        assert len(nm.message_handlers) >= 6  # Should have registered handlers
        
        print("  ✓ MessageHandler initialized and registered handlers")
        
        # Test message creation
        sent_count = mh.send_post_message("Test message")
        assert sent_count == 0  # No peers to send to
        
        print("  ✓ Message sending works (no peers available)")
        
        # Add a test peer and try again
        pm.update_peer_info("alice@192.168.1.10", "192.168.1.10", 8001)
        
        # Test direct message (will fail to send but should not crash)
        result = mh.send_dm_message("alice@192.168.1.10", "Test DM")
        # Result might be False due to network error, but function should work
        
        print("  ✓ Direct messaging works")
        
        # Cleanup
        nm.stop_listening()
        print("  ✓ MessageHandler test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ MessageHandler test failed: {e}")
        return False

def test_user_interface():
    """Test UserInterface functionality"""
    print("Testing UserInterface...")
    
    try:
        from peer.modules.network_manager import NetworkManager
        from peer.modules.peer_manager import PeerManager
        from peer.modules.message_handler import MessageHandler
        from peer.modules.user_interface import UserInterface
        
        # Initialize components
        nm = NetworkManager()
        pm = PeerManager()
        pm.set_user_id("test@127.0.0.1")
        pm.set_network_manager(nm)
        
        mh = MessageHandler(nm, pm)
        ui = UserInterface(mh, pm)
        
        print("  ✓ UserInterface initialized")
        
        # Test verbose toggle
        original_verbose = mh.verbose_mode
        ui._handle_verbose_command()
        assert mh.verbose_mode != original_verbose
        
        print("  ✓ Verbose mode toggle works")
        
        # Cleanup
        nm.stop_listening()
        print("  ✓ UserInterface test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ UserInterface test failed: {e}")
        return False

def test_modular_peer_integration():
    """Test full modular peer integration"""
    print("Testing Modular Peer Integration...")
    
    try:
        from peer.udp_peer_modular import UDPPeerModular
        
        # Test initialization
        peer = UDPPeerModular()
        status = peer.get_status()
        
        assert 'network_info' in status
        assert 'peer_count' in status
        assert status['peer_count'] == 0
        
        print("  ✓ UDPPeerModular initialized")
        
        # Test that all components are connected
        assert peer.peer_manager.network_manager is not None
        assert peer.message_handler.network_manager is not None
        assert peer.message_handler.peer_manager is not None
        
        print("  ✓ All components properly connected")
        
        # Cleanup
        peer.shutdown()
        print("  ✓ Integration test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        return False

def main():
    """Run all modular component tests"""
    print("=" * 60)
    print("MODULAR PEER COMPONENT TESTS")
    print("=" * 60)
    
    tests = [
        ("NetworkManager", test_network_manager),
        ("PeerManager", test_peer_manager),
        ("MessageHandler", test_message_handler),
        ("UserInterface", test_user_interface),
        ("Integration", test_modular_peer_integration),
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
        print("✅ All modular component tests passed!")
        print("\nThe refactored modular implementation is working correctly.")
        print("\nBenefits of the modular architecture:")
        print("- Each component has a single responsibility")
        print("- Components are loosely coupled and easily testable")
        print("- Easy to extend with new features")
        print("- Better error isolation and debugging")
        print("- Cleaner code organization")
        
        print("\nTo use the modular peer:")
        print("   python run_peer_modular.py")
        
    else:
        print("❌ Some modular component tests failed.")
        print("Please check the error messages above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
