#!/usr/bin/env python3
"""
Test script for DM functionality
"""
import sys
import os

# Add the parent directory to Python path to access protocol module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

def test_dm_message_format():
    """Test DM message encoding/decoding"""
    print("Testing DM message format...")
    
    # Create a sample DM message
    dm_data = {
        'TYPE': 'DM',
        'FROM': 'alice@192.168.1.11',
        'TO': 'bob@192.168.1.12',
        'CONTENT': 'Hi Bob!',
        'TIMESTAMP': '1728938500',
        'MESSAGE_ID': 'f83d2b1d',
        'TOKEN': 'alice@192.168.1.11|1728942100|chat'
    }
    
    # Encode the message
    encoded = Protocol.encode_message(dm_data)
    print(f"Encoded DM message:\n{encoded.decode()}")
    
    # Decode the message
    decoded = Protocol.decode_message(encoded)
    print(f"Decoded DM message: {decoded}")
    
    # Verify all fields are preserved
    assert decoded['TYPE'] == 'DM'
    assert decoded['FROM'] == 'alice@192.168.1.11'
    assert decoded['TO'] == 'bob@192.168.1.12'
    assert decoded['CONTENT'] == 'Hi Bob!'
    
    print("[PASS] DM message format test passed!")

def test_post_message_format():
    """Test POST message encoding/decoding"""
    print("\nTesting POST message format...")
    
    # Create a sample POST message
    post_data = {
        'TYPE': 'POST',
        'USER_ID': 'alice@192.168.1.11',
        'CONTENT': 'Hello everyone!',
        'TTL': '3600',
        'MESSAGE_ID': 'a1b2c3d4',
        'TOKEN': 'alice@192.168.1.11|1728942100|broadcast'
    }
    
    # Encode the message
    encoded = Protocol.encode_message(post_data)
    print(f"Encoded POST message:\n{encoded.decode()}")
    
    # Decode the message
    decoded = Protocol.decode_message(encoded)
    print(f"Decoded POST message: {decoded}")
    
    # Verify all fields are preserved
    assert decoded['TYPE'] == 'POST'
    assert decoded['USER_ID'] == 'alice@192.168.1.11'
    assert decoded['CONTENT'] == 'Hello everyone!'
    
    print("[PASS] POST message format test passed!")

if __name__ == "__main__":
    test_dm_message_format()
    test_post_message_format()
    print("\n[PASS] All tests passed! DM implementation is ready to use.")
    print("\nUsage instructions for P2P:")
    print("1. Start peer(s): python ../run_peer.py (in multiple terminals)")
    print("2. Wait for peer discovery (a few seconds)")
    print("3. Use 'LIST' command to see discovered peers")
    print("4. Use 'DM' command to send direct messages")
    print("5. Use 'POST' command to broadcast messages")
    print("6. No server needed - peers communicate directly!")
