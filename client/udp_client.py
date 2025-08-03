# 
import socket
import threading
import random
import secrets
import time
import sys
import os
import base64
import mimetypes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

encode_message = Protocol.encode_message
decode_message = Protocol.decode_message

client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

name = input("User: ")

# Verbose mode setting
verbose_mode = input("Enable verbose mode? (y/n, default=y): ").strip().lower()
verbose_mode = verbose_mode != 'n'  # Default to True unless explicitly 'n'
print(f"Verbose mode: {'ON' if verbose_mode else 'OFF'}")

# Profile storage to remember display names and avatars
user_profiles = {}  # user_id -> {'display_name': str, 'avatar': bool, 'avatar_type': str}

def update_user_profile(user_id, display_name=None, has_avatar=False, avatar_type=''):
    """Update stored user profile information"""
    if user_id not in user_profiles:
        user_profiles[user_id] = {'display_name': '', 'avatar': False, 'avatar_type': ''}
    
    if display_name:
        user_profiles[user_id]['display_name'] = display_name
    user_profiles[user_id]['avatar'] = has_avatar
    user_profiles[user_id]['avatar_type'] = avatar_type

def get_display_name(user_id):
    """Get display name for a user, fallback to user_id if not available"""
    if user_id in user_profiles and user_profiles[user_id]['display_name']:
        return user_profiles[user_id]['display_name']
    return user_id

def get_avatar_info(user_id):
    """Get avatar information for a user"""
    if user_id in user_profiles and user_profiles[user_id]['avatar']:
        return f" 📷({user_profiles[user_id]['avatar_type']})"
    return ""

# Receives messages that is threaded
def receive():
    while True:
        try:
            message, _ = client.recvfrom(65536)  # Increased buffer size for avatar data
            try:
                # Try to decode as protocol message
                msg_dict = decode_message(message)
                msg_type = msg_dict.get('TYPE', '')
                
                if msg_type == 'POST':
                    user_id = msg_dict.get('USER_ID', 'Unknown')
                    content = msg_dict.get('CONTENT', '')
                    
                    if verbose_mode:
                        print(f"\n[POST] {user_id}: {content}")
                    else:
                        display_name = get_display_name(user_id)
                        avatar_info = get_avatar_info(user_id)
                        print(f"\n{display_name}{avatar_info}: {content}")
                
                elif msg_type == 'DM':
                    from_user = msg_dict.get('FROM', 'Unknown')
                    content = msg_dict.get('CONTENT', '')
                    
                    if verbose_mode:
                        print(f"\n[DM] From {from_user}: {content}")
                    else:
                        display_name = get_display_name(from_user)
                        avatar_info = get_avatar_info(from_user)
                        print(f"\n💬 {display_name}{avatar_info}: {content}")
                
                elif msg_type == 'ERROR':
                    error_msg = msg_dict.get('MESSAGE', 'Unknown error')
                    if verbose_mode:
                        print(f"\n[ERROR] {error_msg}")
                    else:
                        print(f"\n❌ {error_msg}")
                
                elif msg_type == 'USER_LIST':
                    users = msg_dict.get('USERS', 'No users')
                    count = msg_dict.get('COUNT', '0')
                    if verbose_mode:
                        print(f"\n[ONLINE USERS] ({count} users): {users}")
                    else:
                        print(f"\n👥 Online ({count}): {users}")
                
                elif msg_type == 'PROFILE':
                    user_id = msg_dict.get('USER_ID', 'Unknown')
                    display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
                    status = msg_dict.get('STATUS', '')
                    has_avatar = 'AVATAR_DATA' in msg_dict
                    avatar_type = msg_dict.get('AVATAR_TYPE', '')
                    
                    # Update our profile storage
                    update_user_profile(user_id, display_name, has_avatar, avatar_type)
                    
                    if verbose_mode:
                        print(f"\n[PROFILE UPDATE] {display_name} ({user_id})")
                        print(f"  Status: {status}")
                        if has_avatar:
                            print(f"  Avatar: {avatar_type} (base64 encoded)")
                        else:
                            print("  Avatar: None")
                    else:
                        avatar_emoji = "📷" if has_avatar else ""
                        print(f"\n👤 {display_name} {avatar_emoji}")
                        print(f"   {status}")
                
                else:
                    # Unknown protocol message type
                    if verbose_mode:
                        print(f"\n[UNKNOWN] {message.decode()}")
                    else:
                        print(f"\n❓ {message.decode()}")
                    
            except:
                # If it's not a valid protocol message, just print as raw text
                print(f"\n{message.decode()}")
        except:
            pass
t = threading.Thread(target=receive)
t.start()

# First send to server
client.sendto(f"SIGNUP_TAG:{name}".encode(),("localhost",50999))

#Gets local ip, returns local ip
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
# generates a 64 bit binary in hext format
def generate_message_id():  
    return secrets.token_hex(8)


# This is main loop for sending messages
while  True:
    user_address = get_local_ip()
    
    msg_type = input("What do you want to use (POST/PROFILE/DM/LIST/VERBOSE): ").strip().upper()
    
    # Handle verbose mode toggle
    if msg_type == "VERBOSE":
        verbose_mode = not verbose_mode
        print(f"Verbose mode: {'ON' if verbose_mode else 'OFF'}")
        continue
    # Multiple if checks to determine what format to use for verbose 
    if msg_type == "POST":
        msg = input("Message: ")
        msg_id = generate_message_id()
        timestamp = int(time.time())
        user_id = name+'@'+user_address
        time_and_ttl = 3600+timestamp
        data = {
            'TYPE':'POST',
            'USER_ID':f'{user_id}',
            'CONTENT':f'{msg}',
            'TTL':'3600',
            'MESSAGE_ID' :f'{msg_id}',
            'TOKEN': f'{user_id}|{time_and_ttl}|broadcast'
              }
    elif msg_type == "DM":
        recipient = input("Recipient (username@ip): ")
        msg = input("Message: ")
        msg_id = generate_message_id()
        timestamp = int(time.time())
        user_id = name+'@'+user_address
        time_and_ttl = 3600+timestamp
        data = {
            'TYPE': 'DM',
            'FROM': f'{user_id}',
            'TO': f'{recipient}',
            'CONTENT': f'{msg}',
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': f'{msg_id}',
            'TOKEN': f'{user_id}|{time_and_ttl}|chat'
        }
    elif msg_type == "LIST":
        # Request list of online users
        msg_id = generate_message_id()
        timestamp = int(time.time())
        user_id = name+'@'+user_address
        time_and_ttl = 3600+timestamp
        data = {
            'TYPE': 'LIST_USERS',
            'FROM': f'{user_id}',
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': f'{msg_id}',
            'TOKEN': f'{user_id}|{time_and_ttl}|list'
        }
    elif msg_type == "PROFILE":
        # Create/Update user profile
        display_name = input("Display Name: ").strip()
        if not display_name:
            display_name = name  # Use username as default
        
        status = input("Status message: ").strip()
        if not status:
            status = "Hello from LSNP!"  # Default status
        
        # Ask if user wants to add avatar
        add_avatar = input("Add profile picture? (y/n): ").strip().lower() == 'y'
        
        msg_id = generate_message_id()
        timestamp = int(time.time())
        user_id = name+'@'+user_address
        time_and_ttl = 3600+timestamp
        
        # Base profile data
        data = {
            'TYPE': 'PROFILE',
            'USER_ID': f'{user_id}',
            'DISPLAY_NAME': display_name,
            'STATUS': status,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': f'{msg_id}',
            'TOKEN': f'{user_id}|{time_and_ttl}|profile'
        }
        
        # Add avatar if requested
        if add_avatar:
            avatar_path = input("Enter path to image file (or press Enter to skip): ").strip()
            if avatar_path and os.path.exists(avatar_path):
                try:
                    # Check file size (should be under ~20KB as per RFC)
                    file_size = os.path.getsize(avatar_path)
                    if file_size > 20480:  # 20KB
                        print(f"Warning: File size ({file_size} bytes) is larger than recommended 20KB")
                        continue_anyway = input("Continue anyway? (y/n): ").strip().lower() == 'y'
                        if not continue_anyway:
                            print("Avatar upload cancelled")
                        else:
                            with open(avatar_path, 'rb') as f:
                                avatar_bytes = f.read()
                                avatar_b64 = base64.b64encode(avatar_bytes).decode('utf-8')
                                
                                # Get MIME type
                                mime_type, _ = mimetypes.guess_type(avatar_path)
                                if not mime_type or not mime_type.startswith('image/'):
                                    mime_type = 'image/png'  # Default to PNG
                                
                                data['AVATAR_TYPE'] = mime_type
                                data['AVATAR_ENCODING'] = 'base64'
                                data['AVATAR_DATA'] = avatar_b64
                                print(f"Avatar added: {mime_type}, {len(avatar_b64)} characters")
                    else:
                        # File size is OK
                        with open(avatar_path, 'rb') as f:
                            avatar_bytes = f.read()
                            avatar_b64 = base64.b64encode(avatar_bytes).decode('utf-8')
                            
                            # Get MIME type
                            mime_type, _ = mimetypes.guess_type(avatar_path)
                            if not mime_type or not mime_type.startswith('image/'):
                                mime_type = 'image/png'  # Default to PNG
                            
                            data['AVATAR_TYPE'] = mime_type
                            data['AVATAR_ENCODING'] = 'base64'
                            data['AVATAR_DATA'] = avatar_b64
                            print(f"Avatar added: {mime_type}, {len(avatar_b64)} characters")
                            
                except Exception as e:
                    print(f"Error reading avatar file: {e}")
            elif avatar_path:
                print(f"File not found: {avatar_path}")
        
        print(f"Profile created for {display_name} ({user_id})")
    else:
        print("Invalid command. Use POST, DM, LIST, PROFILE, or VERBOSE")
        continue

    client.sendto(encode_message(data), ("localhost", 50999))
