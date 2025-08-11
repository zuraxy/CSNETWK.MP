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
import base64

# Add parent directories to path for protocol access
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from protocol.protocol import Protocol

# ANSI Color codes for board display
class Colors:
    RED = '\033[91m'      # Red for X
    GREEN = '\033[92m'    # Green for O
    YELLOW = '\033[93m'   # Yellow for usernames
    BLUE = '\033[94m'     # Blue for filenames
    CYAN = '\033[96m'     # Cyan for file transfer messages
    RESET = '\033[0m'     # Reset to default color
    BOLD = '\033[1m'      # Bold text


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
        self.network_manager.register_message_handler('PING', self.handle_ping)
        self.network_manager.register_message_handler('POST', self.handle_post_message)
        self.network_manager.register_message_handler('DM', self.handle_dm_message)
        self.network_manager.register_message_handler('PROFILE', self.handle_profile_message)
        self.network_manager.register_message_handler('PEER_LIST_REQUEST', self.handle_peer_list_request)
        self.network_manager.register_message_handler('PEER_LIST_RESPONSE', self.handle_peer_list_response)
        self.network_manager.register_message_handler('FOLLOW', self.handle_follow_request)
        self.network_manager.register_message_handler('UNFOLLOW', self.handle_unfollow_request)
        self.network_manager.register_message_handler('FOLLOW_RESPONSE', self.handle_follow_response)
        self.network_manager.register_message_handler('UNFOLLOW_RESPONSE', self.handle_unfollow_response)
        
        # Tic-Tac-Toe game message handlers
        self.network_manager.register_message_handler('TICTACTOE_INVITE', self.handle_tictactoe_invite)
        self.network_manager.register_message_handler('TICTACTOE_MOVE', self.handle_tictactoe_move)
        self.network_manager.register_message_handler('TICTACTOE_RESULT', self.handle_tictactoe_result)
        
        # File transfer message handlers
        self.network_manager.register_message_handler('FILE_OFFER', self.handle_file_offer)
        self.network_manager.register_message_handler('FILE_CHUNK', self.handle_file_chunk)
        self.network_manager.register_message_handler('FILE_RECEIVED', self.handle_file_received)
        self.network_manager.register_message_handler('FILE_ACCEPT', self.handle_file_accept)
        self.network_manager.register_message_handler('FILE_REJECT', self.handle_file_reject)
        
        # Game state storage
        self.active_games = {}  # game_id -> game_state
        self.game_counter = 0  # Counter for generating game IDs
        self.pending_invitations = {}  # game_id -> invitation_info
        
        # File transfer state storage
        self.active_file_transfers = {}  # transfer_id -> transfer_state
        self.file_transfer_counter = 0  # Counter for generating transfer IDs
        self.pending_file_offers = {}  # transfer_id -> offer_info
        self.receiving_files = {}  # transfer_id -> received_chunks
    
    def set_verbose_mode(self, verbose):
        """Set verbose mode for message display"""
        self.verbose_mode = verbose
    
    def handle_peer_discovery(self, msg_dict, addr):
        """Handle peer discovery messages"""
        self.peer_manager.handle_peer_discovery(msg_dict, addr)
        
    def handle_ping(self, msg_dict, addr):
        """Handle PING messages according to LSNP protocol"""
        user_id = msg_dict.get('USER_ID', 'Unknown')
        timestamp = msg_dict.get('TIMESTAMP', None)
        
        # Update peer information (similar to discovery but specifically for PING)
        self.peer_manager.update_peer_info(user_id, addr[0], addr[1])
        
        if self.verbose_mode:
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A"
            except Exception:
                ts_str = str(timestamp)
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: PING")
            print(f"TYPE: PING")
            print(f"USER_ID: {user_id}")
    
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
        
        # Only process messages from users you follow
        if not self.peer_manager.is_following(user_id):
            if self.verbose_mode:
                print(f"\n[FILTERED] POST from {user_id} ignored - not following this user")
            return

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
        """Send a broadcast POST message to followers only"""
        message = {
            'TYPE': 'POST',
            'USER_ID': self.peer_manager.user_id,
            'CONTENT': content,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        # Get only peers who follow you
        followers = self.peer_manager.get_followers()
        follower_peers = {}
        
        # Create a filtered dictionary containing only followers
        for user_id in followers:
            if user_id in self.peer_manager.known_peers:
                follower_peers[user_id] = self.peer_manager.known_peers[user_id]
        
        # If no followers, inform the user
        if not follower_peers:
            if self.verbose_mode:
                print(f"No followers to send POST message to")
            return 0
                
        # Broadcast only to followers
        sent_count = self.network_manager.broadcast_to_peers(message, follower_peers)
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
    
    def send_follow_request(self, target_user_id):
        """Send a follow request to another peer"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
        
        message = {
            'TYPE': 'FOLLOW',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def send_unfollow_request(self, target_user_id):
        """Send an unfollow request to another peer"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
        
        # Only send if we are already following
        if not self.peer_manager.is_following(target_user_id):
            return False
            
        message = {
            'TYPE': 'UNFOLLOW',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def send_follow_response(self, target_user_id, status):
        """Send a response to a follow request"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
            
        message = {
            'TYPE': 'FOLLOW_RESPONSE',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'STATUS': str(status).lower(),
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
        
    def send_unfollow_response(self, target_user_id, status):
        """Send a response to an unfollow request"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
            
        message = {
            'TYPE': 'UNFOLLOW_RESPONSE',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'STATUS': str(status).lower(),
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def _generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)

    def handle_follow_request(self, msg_dict, addr):
        """Handle follow request from another peer"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'FOLLOW')
        message_id = msg_dict.get('MESSAGE_ID', '')

        # Only process if this message is for us
        if to_user == self.peer_manager.user_id:
            # Add the user to our followers list
            self.peer_manager.add_follower(from_user)
            
            # Send follow response
            self.send_follow_response(from_user, True)
            
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
                print(f"MESSAGE_ID: {message_id}")
                print(f"✅ {from_user} is now following you")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                print(f"\n[FOLLOW] {display_name} is now following you")

    def handle_unfollow_request(self, msg_dict, addr):
        """Handle unfollow request from another peer"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'UNFOLLOW')
        message_id = msg_dict.get('MESSAGE_ID', '')

        # Only process if this message is for us
        if to_user == self.peer_manager.user_id:
            # Remove the user from our followers list
            self.peer_manager.remove_follower(from_user)
            
            # Send unfollow response
            self.send_unfollow_response(from_user, True)
            
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
                print(f"MESSAGE_ID: {message_id}")
                print(f"✅ {from_user} has unfollowed you")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                print(f"\n[UNFOLLOW] {display_name} has unfollowed you")

    def handle_follow_response(self, msg_dict, addr):
        """Handle response to a follow request"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        status = msg_dict.get('STATUS', 'false').lower() == 'true'
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'FOLLOW_RESPONSE')
        message_id = msg_dict.get('MESSAGE_ID', '')

        # Only process if this message is for us
        if to_user == self.peer_manager.user_id:
            if status:
                # Add the user to our following list
                self.peer_manager.follow_peer(from_user)
                
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
                    print(f"STATUS: {status}")
                    print(f"MESSAGE_ID: {message_id}")
                    print(f"✅ You are now following {from_user}")
                else:
                    display_name = self.peer_manager.get_display_name(from_user)
                    print(f"\n[FOLLOW] You are now following {display_name}")
            else:
                if self.verbose_mode:
                    print(f"\n[FOLLOW] Follow request to {from_user} was rejected")
                else:
                    display_name = self.peer_manager.get_display_name(from_user)
                    print(f"\n[FOLLOW] Follow request to {display_name} was rejected")

    def handle_unfollow_response(self, msg_dict, addr):
        """Handle response to an unfollow request"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        status = msg_dict.get('STATUS', 'false').lower() == 'true'
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'UNFOLLOW_RESPONSE')
        message_id = msg_dict.get('MESSAGE_ID', '')

        # Only process if this message is for us
        if to_user == self.peer_manager.user_id:
            if status:
                # Remove the user from our following list
                self.peer_manager.unfollow_peer(from_user)
                
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
                    print(f"STATUS: {status}")
                    print(f"MESSAGE_ID: {message_id}")
                    print(f"✅ You have unfollowed {from_user}")
                else:
                    display_name = self.peer_manager.get_display_name(from_user)
                    print(f"\n[UNFOLLOW] You have unfollowed {display_name}")
            else:
                if self.verbose_mode:
                    print(f"\n[UNFOLLOW] Unfollow request to {from_user} failed")
                else:
                    display_name = self.peer_manager.get_display_name(from_user)
                    print(f"\n[UNFOLLOW] Unfollow request to {display_name} failed")

    # ==================== TIC-TAC-TOE GAME METHODS ====================
    


    # ==================== HELPER METHODS ====================
