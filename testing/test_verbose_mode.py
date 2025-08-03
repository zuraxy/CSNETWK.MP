#!/usr/bin/env python3
"""
Test script for verbose mode functionality
"""
import sys
import os

# Add the parent directory to Python path to access protocol module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

def test_verbose_mode_simulation():
    """Simulate how messages would look in verbose vs non-verbose mode"""
    
    # Sample user profiles
    user_profiles = {
        'alice@192.168.1.11': {'display_name': 'Alice Johnson', 'avatar': True, 'avatar_type': 'image/png'},
        'bob@192.168.1.12': {'display_name': 'Bob Smith', 'avatar': False, 'avatar_type': ''},
        'charlie@192.168.1.13': {'display_name': '', 'avatar': True, 'avatar_type': 'image/jpeg'}
    }
    
    def get_display_name(user_id):
        if user_id in user_profiles and user_profiles[user_id]['display_name']:
            return user_profiles[user_id]['display_name']
        return user_id
    
    def get_avatar_info(user_id):
        if user_id in user_profiles and user_profiles[user_id]['avatar']:
            return f" [AVATAR]({user_profiles[user_id]['avatar_type']})"
        return ""
    
    # Sample messages
    post_msg = {
        'TYPE': 'POST',
        'USER_ID': 'alice@192.168.1.11',
        'CONTENT': 'Hello everyone! How is everyone doing today?',
        'TTL': '3600',
        'MESSAGE_ID': 'abc123',
        'TOKEN': 'alice@192.168.1.11|1728942100|broadcast'
    }
    
    dm_msg = {
        'TYPE': 'DM',
        'FROM': 'bob@192.168.1.12',
        'TO': 'alice@192.168.1.11',
        'CONTENT': 'Hey Alice! Want to grab coffee later?',
        'TIMESTAMP': '1728938500',
        'MESSAGE_ID': 'def456',
        'TOKEN': 'bob@192.168.1.12|1728942100|chat'
    }
    
    profile_msg = {
        'TYPE': 'PROFILE',
        'USER_ID': 'charlie@192.168.1.13',
        'DISPLAY_NAME': 'Charlie Wilson',
        'STATUS': 'Working on network protocols!',
        'AVATAR_TYPE': 'image/jpeg',
        'AVATAR_ENCODING': 'base64',
        'AVATAR_DATA': 'fake_base64_data_here',
        'TIMESTAMP': '1728938500',
        'MESSAGE_ID': 'ghi789',
        'TOKEN': 'charlie@192.168.1.13|1728942100|profile'
    }
    
    print("=== VERBOSE MODE EXAMPLES ===\n")
    
    # Verbose POST
    print("POST Message (Verbose):")
    print(f"[POST] {post_msg['USER_ID']}: {post_msg['CONTENT']}")
    
    # Verbose DM
    print(f"\nDM Message (Verbose):")
    print(f"[DM] From {dm_msg['FROM']}: {dm_msg['CONTENT']}")
    
    # Verbose PROFILE
    print(f"\nPROFILE Message (Verbose):")
    print(f"[PROFILE UPDATE] {profile_msg['DISPLAY_NAME']} ({profile_msg['USER_ID']})")
    print(f"  Status: {profile_msg['STATUS']}")
    print(f"  Avatar: {profile_msg['AVATAR_TYPE']} (base64 encoded)")
    
    print("\n" + "="*50)
    print("=== NON-VERBOSE MODE EXAMPLES ===\n")
    
    # Non-verbose POST
    print("POST Message (Non-Verbose):")
    user_id = post_msg['USER_ID']
    display_name = get_display_name(user_id)
    avatar_info = get_avatar_info(user_id)
    print(f"{display_name}{avatar_info}: {post_msg['CONTENT']}")
    
    # Non-verbose DM
    print(f"\nDM Message (Non-Verbose):")
    from_user = dm_msg['FROM']
    display_name = get_display_name(from_user)
    avatar_info = get_avatar_info(from_user)
    print(f"[MSG] {display_name}{avatar_info}: {dm_msg['CONTENT']}")
    
    # Non-verbose PROFILE
    print(f"\nPROFILE Message (Non-Verbose):")
    has_avatar = 'AVATAR_DATA' in profile_msg
    avatar_emoji = "[AVATAR]" if has_avatar else ""
    print(f"[USER] {profile_msg['DISPLAY_NAME']} {avatar_emoji}")
    print(f"   {profile_msg['STATUS']}")
    
    print("\n" + "="*50)
    print("=== COMPARISON WITH DIFFERENT USERS ===\n")
    
    # User with no display name
    print("User without display name (charlie@192.168.1.13):")
    print("Verbose: [POST] charlie@192.168.1.13: Just testing the system")
    charlie_avatar = get_avatar_info('charlie@192.168.1.13')
    print(f"Non-Verbose: charlie@192.168.1.13{charlie_avatar}: Just testing the system")
    
    print(f"\nUser with display name and avatar (alice@192.168.1.11):")
    print("Verbose: [POST] alice@192.168.1.11: Another test message")
    alice_display = get_display_name('alice@192.168.1.11')
    alice_avatar = get_avatar_info('alice@192.168.1.11')
    print(f"Non-Verbose: {alice_display}{alice_avatar}: Another test message")

if __name__ == "__main__":
    test_verbose_mode_simulation()
    print("\n[PASS] Verbose mode demonstration complete!")
    print("\nHow to use verbose mode in the client:")
    print("1. When starting client, choose 'n' for 'Enable verbose mode?'")
    print("2. Or use 'VERBOSE' command during runtime to toggle")
    print("3. Verbose OFF = Clean, simple display with display names")
    print("4. Verbose ON = Full technical details with user IDs and message types")
    print("\nTo run the client: python ../run_client.py")
