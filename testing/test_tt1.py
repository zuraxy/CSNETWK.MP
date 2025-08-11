#!/usr/bin/env python3
"""
Test TTL functionality in LSNP
"""
import sys
import os
import time
import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peer.core.message_handler import MessageHandler
from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.config.settings import DEFAULT_POST_TTL

def test_ttl_validation():
    """Test TTL validation logic"""
    print("Testing TTL validation...")
    network_manager = NetworkManager()
    peer_manager = PeerManager()
    message_handler = MessageHandler(network_manager, peer_manager)
    
    # Test valid message (not expired)
    current_time = int(time.time())
    
    print("  Testing valid message (recent timestamp)...")
    valid = message_handler._is_message_valid(str(current_time - 100), str(DEFAULT_POST_TTL))
    print(f"  Valid message test: {'PASSED' if valid else 'FAILED'}")
    
    # Test expired message
    print("  Testing expired message...")
    invalid = not message_handler._is_message_valid(str(current_time - 7200), str(DEFAULT_POST_TTL))
    print(f"  Expired message test: {'PASSED' if invalid else 'FAILED'}")
    
    print("TTL validation tests complete!")

def test_message_storage_and_cleanup():
    """Test message storage with TTL and cleanup"""
    print("Testing message storage and TTL cleanup...")
    network_manager = NetworkManager()
    peer_manager = PeerManager()
    message_handler = MessageHandler(network_manager, peer_manager)
    
    # Create test messages
    print("  Creating test messages...")
    current_time = int(time.time())
    
    valid_msg = {
        'TYPE': 'POST',
        'USER_ID': 'test@localhost',
        'CONTENT': 'Valid message',
        'TIMESTAMP': str(current_time),
        'TTL': str(DEFAULT_POST_TTL),
        'MESSAGE_ID': 'valid-id'
    }
    
    expired_msg = {
        'TYPE': 'POST',
        'USER_ID': 'test@localhost',
        'CONTENT': 'Expired message',
        'TIMESTAMP': str(current_time - 7200),  # 2 hours ago
        'TTL': '3600',  # 1 hour TTL
        'MESSAGE_ID': 'expired-id'
    }
    
    # Store messages
    print("  Storing messages in cache...")
    message_handler._store_message('valid-id', valid_msg)
    message_handler._store_message('expired-id', expired_msg)
    
    # Check storage
    print("  Checking message cache...")
    valid_stored = 'valid-id' in message_handler.message_cache
    expired_stored = 'expired-id' in message_handler.message_cache
    print(f"  Valid message stored: {'PASSED' if valid_stored else 'FAILED'}")
    print(f"  Expired message stored: {'PASSED' if expired_stored else 'FAILED'}")
    
    # Manual cleanup simulation
    print("  Simulating cleanup process...")
    current_time = int(time.time())
    expired_ids = [mid for mid, (_, expiry) in message_handler.message_cache.items() 
                  if expiry <= current_time]
    for mid in expired_ids:
        del message_handler.message_cache[mid]
        
    # Check cleanup results
    valid_after_cleanup = 'valid-id' in message_handler.message_cache
    expired_after_cleanup = 'expired-id' in message_handler.message_cache
    print(f"  Valid message after cleanup: {'PASSED' if valid_after_cleanup else 'FAILED'}")
    print(f"  Expired message removed: {'PASSED' if not expired_after_cleanup else 'FAILED'}")
    
    print("Message storage and TTL cleanup tests complete!")

if __name__ == "__main__":
    print("=== TTL FUNCTIONALITY TEST ===")
    print()
    test_ttl_validation()
    print()
    test_message_storage_and_cleanup()
    print()
    print("All TTL tests completed!")