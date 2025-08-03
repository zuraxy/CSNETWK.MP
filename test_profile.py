#!/usr/bin/env python3
"""
Test script for PROFILE functionality
"""
import sys
import os
import base64
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol.protocol import Protocol

def create_test_image():
    """Create a small test image for avatar testing"""
    # Create a simple 1x1 pixel PNG (minimal valid PNG)
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8j9gAAAABJRU5ErkJggg=='
    )
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        f.write(png_data)
        return f.name

def test_profile_message_format():
    """Test PROFILE message encoding/decoding"""
    print("Testing PROFILE message format...")
    
    # Create a sample PROFILE message without avatar
    profile_data = {
        'TYPE': 'PROFILE',
        'USER_ID': 'dave@192.168.1.10',
        'DISPLAY_NAME': 'Dave',
        'STATUS': 'Exploring LSNP!',
        'TIMESTAMP': '1728938500',
        'MESSAGE_ID': 'f83d2b1d',
        'TOKEN': 'dave@192.168.1.10|1728942100|profile'
    }
    
    # Encode the message
    encoded = Protocol.encode_message(profile_data)
    print(f"Encoded PROFILE message (no avatar):\n{encoded.decode()}")
    
    # Decode the message
    decoded = Protocol.decode_message(encoded)
    print(f"Decoded PROFILE message: {decoded}")
    
    # Verify all fields are preserved
    assert decoded['TYPE'] == 'PROFILE'
    assert decoded['USER_ID'] == 'dave@192.168.1.10'
    assert decoded['DISPLAY_NAME'] == 'Dave'
    assert decoded['STATUS'] == 'Exploring LSNP!'
    
    print("✓ PROFILE message format test passed!")

def test_profile_with_avatar():
    """Test PROFILE message with avatar data"""
    print("\nTesting PROFILE message with avatar...")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Read and encode image
        with open(test_image_path, 'rb') as f:
            avatar_bytes = f.read()
            avatar_b64 = base64.b64encode(avatar_bytes).decode('utf-8')
        
        # Create PROFILE message with avatar
        profile_data = {
            'TYPE': 'PROFILE',
            'USER_ID': 'alice@192.168.1.11',
            'DISPLAY_NAME': 'Alice',
            'STATUS': 'Testing avatars!',
            'AVATAR_TYPE': 'image/png',
            'AVATAR_ENCODING': 'base64',
            'AVATAR_DATA': avatar_b64,
            'TIMESTAMP': '1728938500',
            'MESSAGE_ID': 'a1b2c3d4',
            'TOKEN': 'alice@192.168.1.11|1728942100|profile'
        }
        
        # Encode the message
        encoded = Protocol.encode_message(profile_data)
        print(f"Encoded PROFILE message size: {len(encoded)} bytes")
        
        # Decode the message
        decoded = Protocol.decode_message(encoded)
        
        # Verify all fields are preserved
        assert decoded['TYPE'] == 'PROFILE'
        assert decoded['USER_ID'] == 'alice@192.168.1.11'
        assert decoded['DISPLAY_NAME'] == 'Alice'
        assert decoded['AVATAR_TYPE'] == 'image/png'
        assert decoded['AVATAR_ENCODING'] == 'base64'
        assert decoded['AVATAR_DATA'] == avatar_b64
        
        # Verify avatar can be decoded back
        decoded_avatar = base64.b64decode(decoded['AVATAR_DATA'])
        assert decoded_avatar == avatar_bytes
        
        print("✓ PROFILE message with avatar test passed!")
        print(f"  Avatar size: {len(avatar_bytes)} bytes")
        print(f"  Base64 size: {len(avatar_b64)} characters")
        
    finally:
        # Clean up test file
        os.unlink(test_image_path)

def test_profile_size_limits():
    """Test PROFILE message size considerations"""
    print("\nTesting PROFILE message size limits...")
    
    # Create a larger avatar to test size limits
    large_avatar_data = 'A' * 30000  # ~30KB of data
    
    profile_data = {
        'TYPE': 'PROFILE',
        'USER_ID': 'bob@192.168.1.12',
        'DISPLAY_NAME': 'Bob',
        'STATUS': 'Testing large avatar',
        'AVATAR_TYPE': 'image/png',
        'AVATAR_ENCODING': 'base64',
        'AVATAR_DATA': large_avatar_data,
        'TIMESTAMP': '1728938500',
        'MESSAGE_ID': 'b1a2c3d4',
        'TOKEN': 'bob@192.168.1.12|1728942100|profile'
    }
    
    encoded = Protocol.encode_message(profile_data)
    message_size = len(encoded)
    
    print(f"Large PROFILE message size: {message_size} bytes")
    
    if message_size > 65536:  # UDP buffer limit
        print("⚠️  Warning: Message exceeds recommended UDP buffer size")
    else:
        print("✓ Message size within UDP buffer limits")
    
    # Test if it can be decoded
    decoded = Protocol.decode_message(encoded)
    assert decoded['AVATAR_DATA'] == large_avatar_data
    print("✓ Large PROFILE message encoding/decoding works")

if __name__ == "__main__":
    test_profile_message_format()
    test_profile_with_avatar()
    test_profile_size_limits()
    print("\n✓ All PROFILE tests passed!")
    print("\nUsage instructions:")
    print("1. Start the server: python run_server.py")
    print("2. Start client(s): python run_client.py")
    print("3. Use 'PROFILE' command to create/update your profile")
    print("4. Other clients will see your profile updates automatically")
    print("5. Avatar files should be under ~20KB for best performance")
