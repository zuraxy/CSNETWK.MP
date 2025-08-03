#!/usr/bin/env python3
"""
Message Handler Module
Handles different types of messages (POST, DM, PROFILE, etc.)
"""
import time
import secrets
import json
import sys
import os
import datetime

# Add parent directories to path for protocol access
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from protocol.protocol import Protocol


class MessageHandler:
    """Handles processing and routing of different message types"""
    
    def __init__(self, network_manager, peer_manager, verbose_mode=True):
        self.network_manager = network_manager
        self.peer_manager = peer_manager
        self.verbose_mode = verbose_mode
        
        # Register message handlers with network manager
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all message type handlers"""
        self.network_manager.register_message_handler('PEER_DISCOVERY', self.handle_peer_discovery)
        self.network_manager.register_message_handler('POST', self.handle_post_message)
        self.network_manager.register_message_handler('DM', self.handle_dm_message)
        self.network_manager.register_message_handler('PROFILE', self.handle_profile_message)
        self.network_manager.register_message_handler('PEER_LIST_REQUEST', self.handle_peer_list_request)
        self.network_manager.register_message_handler('PEER_LIST_RESPONSE', self.handle_peer_list_response)
    
    def set_verbose_mode(self, verbose):
        """Set verbose mode for message display"""
        self.verbose_mode = verbose
    
    def handle_peer_discovery(self, msg_dict, addr):
        """Handle peer discovery messages"""
        self.peer_manager.handle_peer_discovery(msg_dict, addr)
    
    def handle_profile_message(self, msg_dict, addr):
        """Handle profile update messages"""
        import datetime

        user_id = msg_dict.get('USER_ID', 'Unknown')
        display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
        status = msg_dict.get('STATUS', '')
        has_avatar = 'AVATAR_DATA' in msg_dict
        avatar_type = msg_dict.get('AVATAR_TYPE', '')
        avatar_encoding = msg_dict.get('AVATAR_ENCODING', '')
        avatar_data = msg_dict.get('AVATAR_DATA', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'PROFILE')

        # Update profile storage
        self.peer_manager.update_user_profile(user_id, display_name, has_avatar, avatar_type)

        if self.verbose_mode:
            # Format timestamp
            if timestamp:
                try:
                    ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    ts_str = str(timestamp)
            else:
                ts_str = "N/A"
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
            print(f"TYPE: {msg_type}")
            print(f"USER_ID: {user_id}")
            print(f"DISPLAY_NAME: {display_name}")
            print(f"STATUS: {status}")
            if has_avatar:
                print(f"AVATAR_TYPE: {avatar_type}")
                print(f"AVATAR_ENCODING: {avatar_encoding}")
                print(f"AVATAR_DATA: {str(avatar_data)[:10]}...")  # Show only the first few chars for brevity
        else:
            avatar_indicator = "[AVATAR]" if has_avatar else ""
            print(f"\n[USER] {display_name} {avatar_indicator}")
            print(f"   {status}")

    def handle_post_message(self, msg_dict, addr):
        """Handle broadcast POST messages"""
        import datetime

        user_id = msg_dict.get('USER_ID', 'Unknown')
        content = msg_dict.get('CONTENT', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'POST')
        ttl = msg_dict.get('TTL', '')
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')

        if self.verbose_mode:
            # Format timestamp
            if timestamp:
                try:
                    ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    ts_str = str(timestamp)
            else:
                ts_str = "N/A"
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
            print(f"TYPE: {msg_type}")
            print(f"USER_ID: {user_id}")
            print(f"CONTENT: {content}")
            print(f"TTL: {ttl}")
            print(f"MESSAGE_ID: {message_id}")
            print(f"TOKEN: {token}")
            # Example token validation (replace with your actual validation logic)
            if token:
                print("✔ Token valid")
        else:
            display_name = self.peer_manager.get_display_name(user_id)
            avatar_info = self.peer_manager.get_avatar_info(user_id)
            print(f"\n{display_name}{avatar_info}: {content}")
    
    def handle_dm_message(self, msg_dict, addr):
        """Handle direct messages"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        content = msg_dict.get('CONTENT', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'DM')
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')

        # Only display if this message is for us
        if to_user == self.peer_manager.user_id:
            if self.verbose_mode:
                # Format timestamp
                if timestamp:
                    try:
                        ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = str(timestamp)
                else:
                    ts_str = "N/A"
                print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
                print(f"TYPE: {msg_type}")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"CONTENT: {content}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"MESSAGE_ID: {message_id}")
                print(f"TOKEN: {token}")
                # Example token validation (replace with your actual validation logic)
                if token:
                    print("✔ Token valid")
                print(f"✔ ACK sent for MESSAGE_ID {message_id}")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                avatar_info = self.peer_manager.get_avatar_info(from_user)
                print(f"\n[MSG] {display_name}{avatar_info}: {content}")
    
    def handle_peer_list_request(self, msg_dict, addr):
        """Handle requests for peer list"""
        requester = msg_dict.get('FROM', '')
        if requester and requester != self.peer_manager.user_id:
            peer_list = self.peer_manager.get_peer_list()
            response = {
                'TYPE': 'PEER_LIST_RESPONSE',
                'FROM': self.peer_manager.user_id,
                'PEERS': json.dumps(peer_list),
                'COUNT': str(len(peer_list)),
                'TIMESTAMP': str(int(time.time())),
                'MESSAGE_ID': self._generate_message_id()
            }
            self.network_manager.send_to_address(response, addr[0], addr[1])
    
    def handle_peer_list_response(self, msg_dict, addr):
        """Handle peer list responses"""
        try:
            peers = json.loads(msg_dict.get('PEERS', '[]'))
            count = msg_dict.get('COUNT', '0')
            
            if self.verbose_mode:
                print(f"\n[PEER LIST] ({count} peers): {', '.join(peers)}")
            else:
                display_names = [self.peer_manager.get_display_name(peer) for peer in peers]
                print(f"\nOnline ({count}): {', '.join(display_names)}")
        except:
            print("\n[ERROR] Could not parse peer list")
    
    def send_post_message(self, content):
        """Send a broadcast POST message"""
        message = {
            'TYPE': 'POST',
            'USER_ID': self.peer_manager.user_id,
            'CONTENT': content,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peers = self.peer_manager.get_all_peers()
        sent_count = self.network_manager.broadcast_to_peers(message, peers)
        return sent_count
    
    def send_dm_message(self, recipient, content):
        """Send a direct message to a specific peer"""
        if not self.peer_manager.is_peer_known(recipient):
            return False
        
        message = {
            'TYPE': 'DM',
            'FROM': self.peer_manager.user_id,
            'TO': recipient,
            'CONTENT': content,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peer_info = self.peer_manager.get_peer_info(recipient)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def send_profile_message(self, display_name, status, avatar_data=None, avatar_type=None):
        """Send a profile update message"""
        message = {
            'TYPE': 'PROFILE',
            'USER_ID': self.peer_manager.user_id,
            'DISPLAY_NAME': display_name,
            'STATUS': status,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        if avatar_data and avatar_type:
            message['AVATAR_TYPE'] = avatar_type
            message['AVATAR_ENCODING'] = 'base64'
            message['AVATAR_DATA'] = avatar_data
        
        # Update our own profile
        has_avatar = avatar_data is not None
        self.peer_manager.update_user_profile(self.peer_manager.user_id, display_name, has_avatar, avatar_type or '')
        
        # Broadcast to all peers
        peers = self.peer_manager.get_all_peers()
        sent_count = self.network_manager.broadcast_to_peers(message, peers)
        return sent_count
    
    def _generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)
