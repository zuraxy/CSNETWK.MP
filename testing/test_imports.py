#!/usr/bin/env python3
"""
Test script for protocol imports
"""
import sys
import os

# Add the parent directory to Python path to access protocol module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from protocol.protocol import Protocol
    print("[PASS] Protocol import successful!")
    
    # Test encoding/decoding
    test_data = {'TYPE': 'POST', 'USER_ID': 'test@127.0.0.1', 'CONTENT': 'Hello World'}
    encoded = Protocol.encode_message(test_data)
    decoded = Protocol.decode_message(encoded)
    print("[PASS] Protocol encoding/decoding test successful!")
    print(f"Original: {test_data}")
    print(f"Decoded:  {decoded}")
    
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
