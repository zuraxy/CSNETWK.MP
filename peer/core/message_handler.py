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
        
        # Like message handlers
        self.network_manager.register_message_handler('LIKE', self.handle_like_message)
        
        # Token revocation handler
        self.network_manager.register_message_handler('REVOKE', self.handle_token_revocation)
    
    def set_verbose_mode(self, verbose):
        """Set verbose mode for message display"""
        self.verbose_mode = verbose
    
    def validate_message_token(self, msg_dict, peer_ip):
        """
        Validate token in a message
        
        Args:
            msg_dict (dict): The message dictionary
            peer_ip (str): The IP address of the sender
            
        Returns:
            tuple: (is_valid, reason) - Validation result and reason if invalid
        """
        # Skip token validation for discovery and profile messages
        message_type = msg_dict.get('TYPE')
        if message_type in ['PEER_DISCOVERY', 'PEER_LIST_REQUEST', 'PEER_LIST_RESPONSE']:
            return True, None
            
        token = msg_dict.get('TOKEN')
        if not token:
            return False, "Missing token"
            
        # Get required scope for this message type
        required_scope = self.peer_manager.get_scope_for_message_type(message_type)
        
        # Validate token
        return self.peer_manager.validate_token(token, required_scope, peer_ip)
    
    def handle_peer_discovery(self, msg_dict, addr):
        """Handle peer discovery messages"""
        self.peer_manager.handle_peer_discovery(msg_dict, addr)
        
    def handle_ping(self, msg_dict, addr):
        """Handle PING messages according to LSNP protocol"""
        user_id = msg_dict.get('USER_ID', 'Unknown')
        timestamp = msg_dict.get('TIMESTAMP', None)
        
        # Skip if the message is from ourselves
        if user_id == self.peer_manager.user_id:
            return
            
        # Skip if this peer has explicitly revoked (quit the network)
        if user_id in self.peer_manager.revoked_peers:
            return
        
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
        
        # Validate token
        is_valid, reason = self.validate_message_token(msg_dict, addr[0])
        if not is_valid:
            if self.verbose_mode:
                print(f"\n[REJECTED] POST from {user_id} - Invalid token: {reason}")
            return
        
        # Only process messages from users you follow
        if not self.peer_manager.is_following(user_id):
            if self.verbose_mode:
                print(f"\n[FILTERED] POST from {user_id} ignored - not following this user")
            return
            
        # Get TTL or use default (3600 seconds = 1 hour)
        try:
            ttl_seconds = int(ttl) if ttl else 3600
        except ValueError:
            ttl_seconds = 3600
            
        # Track this post so we can like it later
        if timestamp:
            self.peer_manager.add_received_post(user_id, timestamp, content, ttl_seconds)

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
        
        # Validate token
        is_valid, reason = self.validate_message_token(msg_dict, addr[0])
        if not is_valid:
            if self.verbose_mode:
                print(f"\n[REJECTED] DM from {from_user} - Invalid token: {reason}")
            return

        # Store the direct message regardless of whether it's for us
        # (we track messages we receive and messages sent to others)
        if timestamp:
            try:
                ts = int(timestamp)
            except Exception:
                ts = int(time.time())
        else:
            ts = int(time.time())
            
        self.peer_manager.store_direct_message(from_user, to_user, content, ts)

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
    
    def send_post_message(self, content, ttl=3600):
        """Send a broadcast POST message to followers only
        
        Args:
            content (str): The content of the post
            ttl (int): Time To Live in seconds. Default is 3600 (1 hour)
        """
        timestamp = str(int(time.time()))
        
        # Create a token with broadcast scope
        token = self._generate_token("broadcast")
        
        message = {
            'TYPE': 'POST',
            'USER_ID': self.peer_manager.user_id,
            'CONTENT': content,
            'TIMESTAMP': timestamp,
            'TTL': str(ttl),
            'MESSAGE_ID': self._generate_message_id(),
            'TOKEN': token
        }
        
        # Track this post in the peer manager
        self.peer_manager.add_post(timestamp, content, ttl)
        
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
        
        timestamp = int(time.time())
        
        # Create a token with chat scope
        token = self._generate_token("chat")
        
        message = {
            'TYPE': 'DM',
            'FROM': self.peer_manager.user_id,
            'TO': recipient,
            'CONTENT': content,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': self._generate_message_id(),
            'TOKEN': token
        }
        
        # Store the outgoing message
        self.peer_manager.store_direct_message(self.peer_manager.user_id, recipient, content, timestamp)
        
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
        
        # Create token with follow scope
        token = self.peer_manager.create_token("follow")
        message_id = self._generate_message_id()
        timestamp = str(int(time.time()))
        
        # Format according to the specified order
        message = {
            'TYPE': 'FOLLOW',
            'MESSAGE_ID': message_id,
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': timestamp,
            'TOKEN': token
        }
        
        # Log the message if in verbose mode
        if self.verbose_mode:
            import datetime
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            peer_info = self.peer_manager.get_peer_info(target_user_id)
            if peer_info:
                print(f"\nSEND > [{ts_str}] To {peer_info['ip']} | Type: FOLLOW")
                print(f"TYPE: FOLLOW")
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {self.peer_manager.user_id}")
                print(f"TO: {target_user_id}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"TOKEN: {token}")
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
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
            
        # Create token with follow scope (uses same scope as follow)
        token = self.peer_manager.create_token("follow")
        message_id = self._generate_message_id()
        timestamp = str(int(time.time()))
        
        # Format according to the specified order
        message = {
            'TYPE': 'UNFOLLOW',
            'MESSAGE_ID': message_id,
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': timestamp,
            'TOKEN': token
        }
        
        # Log the message if in verbose mode
        if self.verbose_mode:
            import datetime
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            peer_info = self.peer_manager.get_peer_info(target_user_id)
            if peer_info:
                print(f"\nSEND > [{ts_str}] To {peer_info['ip']} | Type: UNFOLLOW")
                print(f"TYPE: UNFOLLOW")
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {self.peer_manager.user_id}")
                print(f"TO: {target_user_id}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"TOKEN: {token}")
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def send_follow_response(self, target_user_id, status):
        """Send a response to a follow request"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
        
        message_id = self._generate_message_id()
        timestamp = str(int(time.time()))
            
        # Format according to the specified order
        message = {
            'TYPE': 'FOLLOW_RESPONSE',
            'MESSAGE_ID': message_id,
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': timestamp,
            'STATUS': str(status).lower()
        }
        
        # Log the message if in verbose mode
        if self.verbose_mode:
            import datetime
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            peer_info = self.peer_manager.get_peer_info(target_user_id)
            if peer_info:
                print(f"\nSEND > [{ts_str}] To {peer_info['ip']} | Type: FOLLOW_RESPONSE")
                print(f"TYPE: FOLLOW_RESPONSE")
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {self.peer_manager.user_id}")
                print(f"TO: {target_user_id}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"STATUS: {str(status).lower()}")
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
        
    def send_unfollow_response(self, target_user_id, status):
        """Send a response to an unfollow request"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
        
        message_id = self._generate_message_id()
        timestamp = str(int(time.time()))
            
        # Format according to the specified order
        message = {
            'TYPE': 'UNFOLLOW_RESPONSE',
            'MESSAGE_ID': message_id,
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'TIMESTAMP': timestamp,
            'STATUS': str(status).lower()
        }
        
        # Log the message if in verbose mode
        if self.verbose_mode:
            import datetime
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            peer_info = self.peer_manager.get_peer_info(target_user_id)
            if peer_info:
                print(f"\nSEND > [{ts_str}] To {peer_info['ip']} | Type: UNFOLLOW_RESPONSE")
                print(f"TYPE: UNFOLLOW_RESPONSE")
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {self.peer_manager.user_id}")
                print(f"TO: {target_user_id}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"STATUS: {str(status).lower()}")
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
        
    # Group message sending methods
    def send_group_create(self, group_id, group_name, members):
        """Send a group creation message to all members"""
        # Validate parameters
        if not group_id or not group_name:
            print("Group ID and name are required")
            return 0
            
        # Add current user to members if not already there
        member_set = set(members)
        member_set.add(self.peer_manager.user_id)
        members_str = ','.join(member_set)
        
        # Prepare message
        message = {
            'TYPE': 'GROUP_CREATE',
            'FROM': self.peer_manager.user_id,
            'GROUP_ID': group_id,
            'GROUP_NAME': group_name,
            'MEMBERS': members_str,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        # Process locally to create the group for the current user
        self.handle_group_create(message, ('127.0.0.1', 0))
        
        # Send to all specified members except self
        sent_count = 0
        for member_id in member_set:
            if member_id == self.peer_manager.user_id:
                continue
                
            peer_info = self.peer_manager.get_peer_info(member_id)
            if peer_info:
                if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                    sent_count += 1
                    
        return sent_count
        
        return sent_count
    
    def send_group_update(self, group_id, add_members=None, remove_members=None):
        """Send a group update message to all members"""
        # Validate parameters
        if not group_id:
            print("Group ID is required")
            return 0
            
        # Verify the group exists and user is creator
        group = self.peer_manager.get_group(group_id)
        if not group:
            print(f"Group {group_id} not found")
            return 0
            
        if group['creator'] != self.peer_manager.user_id:
            print("Only the group creator can update members")
            return 0
            
        # Initialize member sets
        add_set = set() if add_members is None else set(add_members)
        remove_set = set() if remove_members is None else set(remove_members)
        
        # Prepare member strings
        add_str = ','.join(add_set) if add_set else ''
        remove_str = ','.join(remove_set) if remove_set else ''
        
        # Prepare message
        message = {
            'TYPE': 'GROUP_UPDATE',
            'FROM': self.peer_manager.user_id,
            'GROUP_ID': group_id,
            'ADD': add_str,
            'REMOVE': remove_str,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        # Process locally first
        self.handle_group_update(message, ('127.0.0.1', 0))
        
        # Send to all current members (including those being added, excluding those being removed)
        members = self.peer_manager.get_group_members(group_id).copy()
        
        # Add new members to recipient list
        members.update(add_set)
        
        # Send message
        sent_count = 0
        for member_id in members:
            if member_id == self.peer_manager.user_id:
                continue
                
            peer_info = self.peer_manager.get_peer_info(member_id)
            if peer_info:
                if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                    sent_count += 1
                    
        return sent_count
    
    def send_group_message(self, group_id, content):
        """Send a message to a group"""
        # Validate parameters
        if not group_id or not content:
            print("Group ID and message content are required")
            return 0
            
        # Verify the group exists and user is a member
        if not self.peer_manager.is_in_group(group_id):
            print(f"You are not a member of group {group_id}")
            return 0
            
        # Get the group name
        group_name = self.peer_manager.get_group_name(group_id) or group_id
        
        # Generate timestamp
        timestamp = int(time.time())
        
        # Create a token with group scope
        token = self._generate_token("group")
        
        # Prepare message
        message = {
            'TYPE': 'GROUP_MESSAGE',
            'FROM': self.peer_manager.user_id,
            'GROUP_ID': group_id,
            'CONTENT': content,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': self._generate_message_id(),
            'TOKEN': token
        }
        
        # Store the message locally
        self.peer_manager.store_group_message(group_id, self.peer_manager.user_id, content, timestamp)
        
        # Process locally first (show in own chat)
        self.handle_group_message(message, ('127.0.0.1', 0))
        
        # Send to all members except self
        members = self.peer_manager.get_group_members(group_id)
        sent_count = 0
        
        for member_id in members:
            if member_id == self.peer_manager.user_id:
                continue
                
            peer_info = self.peer_manager.get_peer_info(member_id)
            if peer_info:
                if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                    sent_count += 1
                    
        return sent_count
        # Check if group exists and we are a member
        if not self.peer_manager.is_group_member(group_id):
            return 0
            
        # Get group members
        members = self.peer_manager.get_group_members(group_id)
        
        # Prepare message
        message = {
            'TYPE': 'GROUP_MESSAGE',
            'FROM': self.peer_manager.user_id,
            'GROUP_ID': group_id,
            'CONTENT': content,
            'TIMESTAMP': str(int(time.time())),
            'TOKEN': f"{self.peer_manager.user_id}|{int(time.time()) + 3600}|group",  # Simple token with 1-hour expiry
            'MESSAGE_ID': self._generate_message_id()
        }
        
        # Send to all members except self
        sent_count = 0
        for member_id in members:
            if member_id == self.peer_manager.user_id:
                continue
                
            if self.peer_manager.is_peer_known(member_id):
                peer_info = self.peer_manager.get_peer_info(member_id)
                if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                    sent_count += 1
        
        return sent_count
    
    def _generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)
        
    def list_dms_from_peer(self, peer_id):
        """List all direct messages exchanged with a specific peer"""
        if not self.peer_manager.is_peer_known(peer_id):
            return False, f"Peer {peer_id} is not known"
            
        messages = self.peer_manager.get_direct_messages(peer_id)
        if not messages:
            return True, f"No direct messages exchanged with {peer_id}"
            
        # Get display name for the peer
        display_name = self.peer_manager.get_display_name(peer_id)
        
        # Format and return messages
        print(f"\n===== Direct Messages with {display_name} ({peer_id}) =====")
        
        for msg in messages:
            from_user = msg['from_user']
            content = msg['content']
            timestamp = msg['timestamp']
            
            # Format timestamp
            ts_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Determine direction
            if from_user == self.peer_manager.user_id:
                print(f"[{ts_str}] You → {display_name}: {content}")
            else:
                print(f"[{ts_str}] {display_name} → You: {content}")
                
        print(f"===== End of Messages ({len(messages)} total) =====")
        return True, f"Found {len(messages)} messages with {peer_id}"
        
    def list_my_groups(self):
        """List all groups the user belongs to"""
        my_groups = self.peer_manager.get_my_groups()
        
        if not my_groups:
            print("You are not a member of any groups.")
            return False, "No groups found"
            
        print(f"\n===== Your Groups ({len(my_groups)}) =====")
        for i, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if not group:
                continue
                
            creator_status = " (Creator)" if group['creator'] == self.peer_manager.user_id else ""
            member_count = len(group['members'])
            message_count = len(self.peer_manager.group_messages.get(group_id, []))
            
            print(f"{i}. {group['name']} (ID: {group_id}){creator_status}")
            print(f"   Members: {member_count} | Messages: {message_count}")
            
        print("===== End of Groups =====")
        return True, f"Found {len(my_groups)} groups"
        
    def show_group_members(self, group_id):
        """Show all members of a specific group"""
        group = self.peer_manager.get_group(group_id)
        if not group:
            print(f"Group {group_id} not found")
            return False, "Group not found"
            
        # Show group details
        creator_id = group['creator']
        creator_name = self.peer_manager.get_display_name(creator_id) or creator_id
        
        print(f"\n===== Group: {group['name']} (ID: {group_id}) =====")
        print(f"Created by: {creator_name} ({creator_id})")
        
        # Format creation timestamp
        created_at = group['created_at']
        try:
            created_str = datetime.datetime.fromtimestamp(int(created_at)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_str = str(created_at)
        
        print(f"Created on: {created_str}")
        print(f"\nMembers ({len(group['members'])}):")
        
        # List all members
        for member_id in group['members']:
            display_name = self.peer_manager.get_display_name(member_id) or member_id
            you_marker = " (You)" if member_id == self.peer_manager.user_id else ""
            creator_marker = " (Creator)" if member_id == creator_id else ""
            print(f"  - {display_name} ({member_id}){you_marker}{creator_marker}")
            
        print("===== End of Members =====")
        return True, f"Found {len(group['members'])} members in group {group_id}"
        
    def show_group_messages(self, group_id, limit=20):
        """Show messages in a specific group"""
        if not self.peer_manager.is_in_group(group_id):
            print(f"You are not a member of group {group_id}")
            return False, "Not a member of this group"
            
        messages = self.peer_manager.get_group_messages(group_id)
        if not messages:
            print(f"No messages found in group {group_id}")
            return False, "No messages found"
            
        group_name = self.peer_manager.get_group_name(group_id) or group_id
        
        print(f"\n===== Messages in {group_name} (ID: {group_id}) =====")
        
        # Show only the last 'limit' messages if there are more
        if len(messages) > limit:
            print(f"Showing the last {limit} of {len(messages)} messages...")
            messages = messages[-limit:]
        
        for msg in messages:
            from_user = msg['from_user']
            content = msg['content']
            timestamp = msg['timestamp']
            
            # Format timestamp
            ts_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format sender info
            display_name = self.peer_manager.get_display_name(from_user) or from_user
            you_marker = " (You)" if from_user == self.peer_manager.user_id else ""
            
            print(f"[{ts_str}] {display_name}{you_marker}: {content}")
            
        print(f"===== End of Messages ({len(messages)} total) =====")
        return True, f"Found {len(messages)} messages in group {group_id}"
        
    def _generate_token(self, scope=None):
        """
        Generate a security token for messages
        
        Args:
            scope (str, optional): The scope of the token. If None, will determine based on context.
            
        Returns:
            str: Formatted token string
        """
        if scope is None:
            # This is a fallback only - specific methods should specify the scope
            scope = "broadcast"
        
        return self.peer_manager.create_token(scope)

    def handle_follow_request(self, msg_dict, addr):
        """Handle follow request from another peer"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        msg_type = msg_dict.get('TYPE', 'FOLLOW')
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')
        
        # Validate token
        is_valid, reason = self.validate_message_token(msg_dict, addr[0])
        if not is_valid:
            if self.verbose_mode:
                print(f"\n[REJECTED] FOLLOW from {from_user} - Invalid token: {reason}")
            return

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
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"TIMESTAMP: {timestamp}")
                if token:
                    print(f"TOKEN: {token}")
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
        token = msg_dict.get('TOKEN', '')
        
        # Validate token
        is_valid, reason = self.validate_message_token(msg_dict, addr[0])
        if not is_valid:
            if self.verbose_mode:
                print(f"\n[REJECTED] UNFOLLOW from {from_user} - Invalid token: {reason}")
            return

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
                print(f"MESSAGE_ID: {message_id}")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"TIMESTAMP: {timestamp}")
                if 'TOKEN' in msg_dict:
                    print(f"TOKEN: {msg_dict.get('TOKEN')}")
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
                    print(f"MESSAGE_ID: {message_id}")
                    print(f"FROM: {from_user}")
                    print(f"TO: {to_user}")
                    print(f"TIMESTAMP: {timestamp}")
                    print(f"STATUS: {status}")
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
                    print(f"MESSAGE_ID: {message_id}")
                    print(f"FROM: {from_user}")
                    print(f"TO: {to_user}")
                    print(f"TIMESTAMP: {timestamp}")
                    print(f"STATUS: {status}")
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
                    
    # Group message handlers
    def handle_group_create(self, msg_dict, addr):
        """Handle group creation messages"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        group_id = msg_dict.get('GROUP_ID', '')
        group_name = msg_dict.get('GROUP_NAME', '')
        members_str = msg_dict.get('MEMBERS', '')
        timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
        
        # Parse members list
        if members_str:
            members = set(member.strip() for member in members_str.split(',') if member.strip())
        else:
            members = set()
            
        # Always include creator
        members.add(from_user)
        
        if self.verbose_mode:
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = str(timestamp)
                
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_CREATE")
            print(f"FROM: {from_user}")
            print(f"GROUP_ID: {group_id}")
            print(f"GROUP_NAME: {group_name}")
            print(f"MEMBERS: {members_str}")
            print(f"TIMESTAMP: {timestamp}")
        else:
            print(f"\nYou've been added to {group_name}")
            
        # Add group to peer manager
        self.peer_manager.add_group(group_id, group_name, from_user, members, int(timestamp))
    
    def handle_group_update(self, msg_dict, addr):
        """Handle group update messages"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        group_id = msg_dict.get('GROUP_ID', '')
        add_members_str = msg_dict.get('ADD', '')
        remove_members_str = msg_dict.get('REMOVE', '')
        timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
        
        # Parse add/remove lists
        add_members = set(member.strip() for member in add_members_str.split(',') if member.strip())
        remove_members = set(member.strip() for member in remove_members_str.split(',') if member.strip())
        
        if self.verbose_mode:
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = str(timestamp)
                
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_UPDATE")
            print(f"FROM: {from_user}")
            print(f"GROUP_ID: {group_id}")
            if add_members:
                print(f"ADD: {add_members_str}")
            if remove_members:
                print(f"REMOVE: {remove_members_str}")
            print(f"TIMESTAMP: {timestamp}")
        else:
            group_name = self.peer_manager.get_group_name(group_id) or group_id
            print(f"\nThe group \"{group_name}\" member list was updated.")
            
        # Update group in peer manager
        self.peer_manager.update_group(group_id, from_user, add_members, remove_members)
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        group_id = msg_dict.get('GROUP_ID', '')
        add_members_str = msg_dict.get('ADD', '')
        remove_members_str = msg_dict.get('REMOVE', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        token = msg_dict.get('TOKEN', '')
        msg_type = msg_dict.get('TYPE', 'GROUP_UPDATE')
        message_id = msg_dict.get('MESSAGE_ID', '')
        
        # Parse member lists
        add_members = add_members_str.split(',') if add_members_str else []
        remove_members = remove_members_str.split(',') if remove_members_str else []
        
        # Check if we know about this group
        group = self.peer_manager.get_group(group_id)
        if not group:
            return
            
        # Check if update is from group creator
        if group['creator'] != from_user:
            if self.verbose_mode:
                print(f"\n[ERROR] Group update from non-creator {from_user} rejected")
            return
            
        # Check if we are being removed
        if self.peer_manager.user_id in remove_members:
            success, message = self.peer_manager.leave_group(group_id)
            if success and not self.verbose_mode:
                print(f"\nYou've been removed from the group \"{group['name']}\"")
            return
            
        # Apply updates to local group
        # Add new members
        for member in add_members:
            if member not in group['members']:
                group['members'].append(member)
                
        # Remove members
        for member in remove_members:
            if member in group['members'] and member != group['creator']:
                group['members'].remove(member)
        
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
            print(f"GROUP_ID: {group_id}")
            print(f"ADD: {add_members_str}")
            print(f"REMOVE: {remove_members_str}")
            print(f"TIMESTAMP: {timestamp}")
            print(f"TOKEN: {token}")
            print(f"MESSAGE_ID: {message_id}")
            print(f"✅ Group updated successfully")
        else:
            print(f"\nThe group \"{group['name']}\" member list was updated.")
    
    def handle_group_message(self, msg_dict, addr):
        """Handle messages to groups"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        group_id = msg_dict.get('GROUP_ID', '')
        content = msg_dict.get('CONTENT', '')
        timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
        token = msg_dict.get('TOKEN', '')
        
        # Validate token - local messages (from self) skip validation
        if addr[0] != '127.0.0.1':
            is_valid, reason = self.validate_message_token(msg_dict, addr[0])
            if not is_valid:
                if self.verbose_mode:
                    print(f"\n[REJECTED] GROUP_MESSAGE from {from_user} - Invalid token: {reason}")
                return
        
        # Verify this is a valid group and we're a member
        if not self.peer_manager.is_in_group(group_id):
            # Not a member, ignore the message
            return
            
        # Store the group message
        self.peer_manager.store_group_message(group_id, from_user, content, timestamp)
            
        # Get group and sender info
        group_name = self.peer_manager.get_group_name(group_id) or group_id
        display_name = self.peer_manager.get_display_name(from_user) or from_user
        
        if self.verbose_mode:
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = str(timestamp)
                
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_MESSAGE")
            print(f"FROM: {from_user}")
            print(f"GROUP_ID: {group_id}")
            print(f"GROUP_NAME: {group_name}")
            print(f"CONTENT: {content}")
            print(f"TIMESTAMP: {timestamp}")
        else:
            # User-friendly format
            print(f"\n[{group_name}] {display_name}: {content}")
    
    # Like/Unlike message handling
    def handle_like_message(self, msg_dict, addr):
        """Handle like/unlike messages"""
        import datetime

        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', 'Unknown')
        post_timestamp = msg_dict.get('POST_TIMESTAMP', '')
        action = msg_dict.get('ACTION', 'LIKE')
        timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
        token = msg_dict.get('TOKEN', '')
        
        # Only process if this is for our post
        if to_user != self.peer_manager.user_id:
            return
        
        # Verify post exists
        post_content = self.peer_manager.get_post_content(post_timestamp)
        if not post_content and action == 'LIKE':
            # Post doesn't exist, ignore like
            return
            
        # Handle the like/unlike
        display_name = self.peer_manager.get_display_name(from_user) or from_user
        
        if self.verbose_mode:
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = str(timestamp)
                
            post_ts_str = "Unknown"
            try:
                post_ts_str = datetime.datetime.fromtimestamp(int(post_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                post_ts_str = str(post_timestamp)
                
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: LIKE")
            print(f"FROM: {from_user}")
            print(f"TO: {to_user}")
            print(f"POST_TIMESTAMP: {post_timestamp} ({post_ts_str})")
            print(f"ACTION: {action}")
            print(f"TIMESTAMP: {timestamp}")
            print(f"TOKEN: {token}")
        else:
            # User-friendly format
            truncated_post = post_content[:30] + ("..." if len(post_content) > 30 else "")
            if action == 'LIKE':
                print(f"\n{display_name} likes your post \"{truncated_post}\"")
            else:
                print(f"\n{display_name} unliked your post \"{truncated_post}\"")
        
        # Update likes in peer manager
        if action == 'LIKE':
            self.peer_manager.like_post(to_user, post_timestamp)
        else:
            self.peer_manager.unlike_post(to_user, post_timestamp)
            
    def send_like_message(self, post_author, post_timestamp, action='LIKE'):
        """Send a like/unlike message to a post author
        
        Args:
            post_author (str): User ID of the post author
            post_timestamp (str): Timestamp of the post to like/unlike
            action (str): Either 'LIKE' or 'UNLIKE'
        
        Returns:
            bool: True if the message was sent, False otherwise
        """
        # Verify the author is known
        if post_author not in self.peer_manager.known_peers:
            print(f"\n[ERROR] Unknown user {post_author}")
            return False
            
        # Create the message
        message = {
            'TYPE': 'LIKE',
            'FROM': self.peer_manager.user_id,
            'TO': post_author,
            'POST_TIMESTAMP': post_timestamp,
            'ACTION': action,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id(),
            'TOKEN': self._generate_token()  # Optional security token
        }
        
        # Update local state
        if action == 'LIKE':
            self.peer_manager.like_post(post_author, post_timestamp)
        else:
            self.peer_manager.unlike_post(post_author, post_timestamp)
            
        # Send the message to the post author
        peer_info = self.peer_manager.get_peer_info(post_author)
        if peer_info:
            success = self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
            
            if success:
                if self.verbose_mode:
                    print(f"\n[LIKE] {'Liked' if action == 'LIKE' else 'Unliked'} post from {post_author} ({post_timestamp})")
                    
                return True
            else:
                print(f"\n[ERROR] Failed to send {'like' if action == 'LIKE' else 'unlike'} message to {post_author}")
                return False
        else:
            print(f"\n[ERROR] Could not find address for {post_author}")
            return False


    def send_tictactoe_invite(self, target_user_id, chosen_symbol='X', first_move_position=None):
        """Send a Tic-Tac-Toe game invitation to another peer"""
        if not self.peer_manager.is_peer_known(target_user_id):
            return False
        
        game_id = self._generate_game_id()
        
        # Set up players based on chosen symbol
        if chosen_symbol == 'X':
            player_x = self.peer_manager.user_id
            player_o = target_user_id
            current_turn = 'X'
        else:  # chosen_symbol == 'O'
            player_x = target_user_id
            player_o = self.peer_manager.user_id
            current_turn = 'X'  # X always goes first
        
        # Initialize board
        board = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        
        # If choosing X and making first move
        if chosen_symbol == 'X' and first_move_position is not None:
            if not self._is_valid_move(board, first_move_position):
                return False  # Invalid first move
            board[first_move_position] = 'X'
            current_turn = 'O'  # Switch to O's turn
        
        message = {
            'TYPE': 'TICTACTOE_INVITE',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'GAMEID': game_id,
            'MESSAGE_ID': self._generate_message_id(),
            'SYMBOL': chosen_symbol,
            'TIMESTAMP': str(int(time.time())),
            'TOKEN': f"{self.peer_manager.user_id}|{int(time.time())}|game",
            'BOARD': ','.join(board)
        }
        
        # Initialize game state
        self.active_games[game_id] = {
            'player_x': player_x,
            'player_o': player_o,
            'board': board,
            'current_turn': current_turn,
            'status': 'waiting_for_response',
            'turn_number': 1 if first_move_position is not None else 1
        }
        
        peer_info = self.peer_manager.get_peer_info(target_user_id)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def send_tictactoe_move(self, game_id, position):
        """Send a Tic-Tac-Toe move"""
        if game_id not in self.active_games:
            return False
        
        game = self.active_games[game_id]
        current_player = self.peer_manager.user_id
        
        # Determine if we are X or O
        if current_player == game['player_x']:
            player_symbol = 'X'
            opponent = game['player_o']
        else:
            player_symbol = 'O'
            opponent = game['player_x']
        
        # Validate it's our turn
        if game['current_turn'] != player_symbol:
            return False
        
        # Validate position is available
        if not self._is_valid_move(game['board'], position):
            return False
        
        # Make the move
        game['board'][position] = player_symbol
        
        # Check for win or draw
        result = self._check_game_result(game['board'])
        
        # Increment turn number
        game['turn_number'] = game.get('turn_number', 1) + 1
        
        message = {
            'TYPE': 'TICTACTOE_MOVE',
            'FROM': self.peer_manager.user_id,
            'TO': opponent,
            'GAMEID': game_id,
            'MESSAGE_ID': self._generate_message_id(),
            'POSITION': str(position),
            'SYMBOL': player_symbol,
            'TURN': str(game['turn_number']),
            'TOKEN': f"{self.peer_manager.user_id}|{int(time.time())}|game"
        }
        
        # Switch turns
        game['current_turn'] = 'O' if player_symbol == 'X' else 'X'
        
        # If game ended, send result
        if result['finished']:
            game['status'] = 'finished'
            self._send_game_result(game_id, result, opponent)
        
        peer_info = self.peer_manager.get_peer_info(opponent)
        if peer_info:
            return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
        return False
    
    def handle_tictactoe_invite(self, msg_dict, addr):
        """Handle incoming Tic-Tac-Toe game invitation"""
        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        game_id = msg_dict.get('GAMEID', '')
        inviter_symbol = msg_dict.get('SYMBOL', 'X')
        board_str = msg_dict.get('BOARD', '0,1,2,3,4,5,6,7,8')
        timestamp = msg_dict.get('TIMESTAMP', None)
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')
        
        # Only process if this invitation is for us
        if to_user == self.peer_manager.user_id:
            # Set up players based on inviter's choice
            if inviter_symbol == 'X':
                player_x = from_user
                player_o = self.peer_manager.user_id
                our_symbol = 'O'
                their_symbol = 'X'
            else:  # inviter_symbol == 'O'
                player_x = self.peer_manager.user_id
                player_o = from_user
                our_symbol = 'X'
                their_symbol = 'O'
            
            # Parse board
            board = board_str.split(',')
            
            # Determine current turn (X always goes first, but board might already have moves)
            x_moves = sum(1 for cell in board if cell == 'X')
            o_moves = sum(1 for cell in board if cell == 'O')
            current_turn = 'X' if x_moves == o_moves else 'O'
            
            # Store the game state
            self.active_games[game_id] = {
                'player_x': player_x,
                'player_o': player_o,
                'board': board,
                'current_turn': current_turn,
                'status': 'active',
                'turn_number': x_moves + o_moves + 1
            }
            
            if self.verbose_mode:
                # Format timestamp
                if timestamp:
                    try:
                        ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = str(timestamp)
                else:
                    ts_str = "N/A"
                
                print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: TICTACTOE_INVITE")
                print(f"TYPE: TICTACTOE_INVITE")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"GAMEID: {game_id}")
                print(f"MESSAGE_ID: {message_id}")
                print(f"SYMBOL: {inviter_symbol}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"TOKEN: {token}")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                print(f"\n🎮 [GAME] {display_name} invited you to play Tic-Tac-Toe!")
            
            print(f"Game ID: {game_id}")
            print(f"You are '{our_symbol}', they are '{their_symbol}'")
            
            # Show current board state
            self._display_board(board)
            
            # Check if it's already our turn (in case they made first move as X)
            if current_turn == our_symbol:
                print(f"It's your turn! Use: GAME {game_id} <position>")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                print(f"Waiting for {display_name} ({their_symbol}) to make their move.")
    
    def handle_tictactoe_move(self, msg_dict, addr):
        """Handle incoming Tic-Tac-Toe move"""
        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        game_id = msg_dict.get('GAMEID', '')
        position = int(msg_dict.get('POSITION', 0))
        symbol = msg_dict.get('SYMBOL', '')
        turn = msg_dict.get('TURN', '1')
        timestamp = msg_dict.get('TIMESTAMP', None)
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')
        
        # Only process if this move is for us
        if to_user == self.peer_manager.user_id and game_id in self.active_games:
            game = self.active_games[game_id]
            
            # Update board with the move
            game['board'][position] = symbol
            
            # Update turn number
            game['turn_number'] = int(turn)
            
            # Update current turn to switch to us (since opponent just played)
            game['current_turn'] = 'O' if symbol == 'X' else 'X'
            
            # Check game result
            result = self._check_game_result(game['board'])
            
            if self.verbose_mode:
                # Format timestamp
                if timestamp:
                    try:
                        ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = str(timestamp)
                else:
                    ts_str = "N/A"
                
                print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: TICTACTOE_MOVE")
                print(f"TYPE: TICTACTOE_MOVE")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"GAMEID: {game_id}")
                print(f"MESSAGE_ID: {message_id}")
                print(f"POSITION: {position}")
                print(f"SYMBOL: {symbol}")
                print(f"TURN: {turn}")
                print(f"TOKEN: {token}")
            else:
                display_name = self.peer_manager.get_display_name(from_user)
                print(f"\n🎮 [GAME] {display_name} played {symbol} at position {position}")
            
            self._display_board(game['board'])
            
            if result['finished']:
                game['status'] = 'finished'
                if result['winner']:
                    if result['winner'] == 'X':
                        winner_name = self.peer_manager.get_display_name(game['player_x'])
                        print(f"🏆 Game Over! {winner_name} (X) wins!")
                    else:
                        winner_name = self.peer_manager.get_display_name(game['player_o'])
                        print(f"🏆 Game Over! {winner_name} (O) wins!")
                else:
                    print("🤝 Game Over! It's a draw!")
                
                # Clean up game
                del self.active_games[game_id]
            else:
                # It's our turn now
                current_player = self.peer_manager.user_id
                if current_player == game['player_x']:
                    your_symbol = 'X'
                else:
                    your_symbol = 'O'
                print(f"Your turn! You are '{your_symbol}'. Use: GAME {game_id} <position>")
    
    def handle_tictactoe_result(self, msg_dict, addr):
        """Handle Tic-Tac-Toe game result"""
        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        game_id = msg_dict.get('GAMEID', '')
        result_type = msg_dict.get('RESULT', '')
        symbol = msg_dict.get('SYMBOL', '')
        winning_line = msg_dict.get('WINNING_LINE', '')
        timestamp = msg_dict.get('TIMESTAMP', None)
        message_id = msg_dict.get('MESSAGE_ID', '')
        
        # Only process if this result is for us
        if to_user == self.peer_manager.user_id and game_id in self.active_games:
            if self.verbose_mode:
                # Format timestamp
                if timestamp:
                    try:
                        ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = str(timestamp)
                else:
                    ts_str = "N/A"
                print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: TICTACTOE_RESULT")
                print(f"TYPE: TICTACTOE_RESULT")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"GAMEID: {game_id}")
                print(f"MESSAGE_ID: {message_id}")
                print(f"RESULT: {result_type}")
                print(f"SYMBOL: {symbol}")
                print(f"WINNING_LINE: {winning_line}")
                print(f"TIMESTAMP: {timestamp}")
            
            game = self.active_games[game_id]
            display_name = self.peer_manager.get_display_name(from_user)
            
            if result_type == 'WIN' and symbol:
                if symbol == 'X':
                    winner_name = self.peer_manager.get_display_name(game['player_x'])
                    print(f"🏆 Game Over! {winner_name} (X) wins!")
                else:
                    winner_name = self.peer_manager.get_display_name(game['player_o'])
                    print(f"🏆 Game Over! {winner_name} (O) wins!")
            elif result_type == 'DRAW':
                print("🤝 Game Over! It's a draw!")
            
            # Clean up game
            del self.active_games[game_id]
    
    def _send_game_result(self, game_id, result, opponent):
        """Send game result to opponent"""
        winning_line = ""
        if result['winning_line']:
            winning_line = ','.join(map(str, result['winning_line']))
        
        message = {
            'TYPE': 'TICTACTOE_RESULT',
            'FROM': self.peer_manager.user_id,
            'TO': opponent,
            'GAMEID': game_id,
            'MESSAGE_ID': self._generate_message_id(),
            'RESULT': 'WIN' if result['winner'] else 'DRAW',
            'SYMBOL': result['winner'] or '',
            'WINNING_LINE': winning_line,
            'TIMESTAMP': str(int(time.time()))
        }
        
        peer_info = self.peer_manager.get_peer_info(opponent)
        if peer_info:
            self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
    
    def _generate_game_id(self):
        """Generate a unique game ID in format gX where X is 0-255"""
        game_id = f"g{self.game_counter}"
        self.game_counter = (self.game_counter + 1) % 256  # Keep within 0-255 range
        return game_id
    
    def _is_valid_move(self, board, position):
        """Check if a move is valid"""
        if position < 0 or position > 8:
            return False
        return board[position] not in ['X', 'O']
    
    def _check_game_result(self, board):
        """Check if the game has ended and return result"""
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] and board[i] in ['X', 'O']:
                return {'finished': True, 'winner': board[i], 'winning_line': [i, i+1, i+2]}
        
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] and board[i] in ['X', 'O']:
                return {'finished': True, 'winner': board[i], 'winning_line': [i, i+3, i+6]}
        
        # Check diagonals
        if board[0] == board[4] == board[8] and board[0] in ['X', 'O']:
            return {'finished': True, 'winner': board[0], 'winning_line': [0, 4, 8]}
        if board[2] == board[4] == board[6] and board[2] in ['X', 'O']:
            return {'finished': True, 'winner': board[2], 'winning_line': [2, 4, 6]}
        
        # Check for draw
        if all(cell in ['X', 'O'] for cell in board):
            return {'finished': True, 'winner': None, 'winning_line': None}
        
        # Game continues
        return {'finished': False, 'winner': None, 'winning_line': None}
    
    def _display_board(self, board):
        """Display the Tic-Tac-Toe board with colored X (red) and O (green)"""
        def colorize_cell(cell):
            if cell == 'X':
                return f"{Colors.BOLD}{Colors.RED}X{Colors.RESET}"
            elif cell == 'O':
                return f"{Colors.BOLD}{Colors.GREEN}O{Colors.RESET}"
            else:
                return cell
        
        print("\n   |   |   ")
        print(f" {colorize_cell(board[0])} | {colorize_cell(board[1])} | {colorize_cell(board[2])} ")
        print("___|___|___")
        print("   |   |   ")
        print(f" {colorize_cell(board[3])} | {colorize_cell(board[4])} | {colorize_cell(board[5])} ")
        print("___|___|___")
        print("   |   |   ")
        print(f" {colorize_cell(board[6])} | {colorize_cell(board[7])} | {colorize_cell(board[8])} ")
        print("   |   |   ")
    
    # File Transfer Methods
    def handle_file_offer(self, msg_dict, addr):
        """Handle FILE_OFFER message"""
        try:
            transfer_id = msg_dict.get('transfer_id')
            filename = msg_dict.get('filename')
            file_size = msg_dict.get('file_size')
            file_type = msg_dict.get('file_type', 'unknown')
            description = msg_dict.get('description', 'No description')
            sender_name = msg_dict.get('sender_name', f"Unknown@{addr[0]}")
            
            if not all([transfer_id, filename, file_size]):
                print(f"{Colors.RED}Error: Invalid file offer received{Colors.RESET}")
                return
            
            # Store the file offer
            self.pending_file_offers[transfer_id] = {
                'filename': filename,
                'file_size': int(file_size),
                'file_type': file_type,
                'description': description,
                'sender_name': sender_name,
                'sender_addr': addr,
                'timestamp': time.time()
            }
            
            print(f"\n{Colors.CYAN}📁 File Offer Received!{Colors.RESET}")
            print(f"From: {Colors.YELLOW}{sender_name}{Colors.RESET}")
            print(f"File: {Colors.BLUE}{filename}{Colors.RESET}")
            print(f"Size: {self._format_file_size(int(file_size))}")
            print(f"Type: {file_type}")
            print(f"Description: {description}")
            print(f"Transfer ID: {transfer_id}")
            print(f"Use 'FILE ACCEPT {transfer_id}' to accept or 'FILE REJECT {transfer_id}' to reject")
            
        except Exception as e:
            print(f"{Colors.RED}Error handling file offer: {e}{Colors.RESET}")
    
    def handle_file_chunk(self, msg_dict, addr):
        """Handle FILE_CHUNK message"""
        try:
            transfer_id = msg_dict.get('transfer_id')
            chunk_number = msg_dict.get('chunk_number')
            total_chunks = msg_dict.get('total_chunks')
            chunk_data = msg_dict.get('chunk_data')
            
            if not all([transfer_id, chunk_number is not None, total_chunks, chunk_data]):
                print(f"{Colors.RED}Error: Invalid file chunk received{Colors.RESET}")
                return
            
            chunk_number = int(chunk_number)
            total_chunks = int(total_chunks)
            
            print(f"Debug: Received chunk {chunk_number}/{total_chunks}, data length: {len(chunk_data)}")
            
            # Initialize receiving file structure if needed
            if transfer_id not in self.receiving_files:
                self.receiving_files[transfer_id] = {
                    'chunks': {},
                    'total_chunks': total_chunks,
                    'received_count': 0,
                    'sender_addr': addr
                }
                print(f"Debug: Initialized receiving structure for {transfer_id}")
            
            # Store the chunk
            if chunk_number not in self.receiving_files[transfer_id]['chunks']:
                self.receiving_files[transfer_id]['chunks'][chunk_number] = chunk_data
                self.receiving_files[transfer_id]['received_count'] += 1
                
                received = self.receiving_files[transfer_id]['received_count']
                print(f"{Colors.CYAN}Receiving chunk {chunk_number + 1}/{total_chunks} ({received}/{total_chunks} total){Colors.RESET}")
                
                # Check if all chunks received
                if received == total_chunks:
                    print(f"Debug: All chunks received, reassembling file...")
                    self._reassemble_file(transfer_id)
            else:
                print(f"Debug: Chunk {chunk_number} already received, skipping")
            
        except Exception as e:
            print(f"{Colors.RED}Error handling file chunk: {e}{Colors.RESET}")
    
    def handle_file_received(self, msg_dict, addr):
        """Handle FILE_RECEIVED confirmation"""
        try:
            transfer_id = msg_dict.get('transfer_id')
            status = msg_dict.get('status')
            receiver_name = msg_dict.get('receiver_name', f"Unknown@{addr[0]}")
            
            if transfer_id in self.active_file_transfers:
                transfer_info = self.active_file_transfers[transfer_id]
                filename = transfer_info.get('filename', 'unknown file')
                
                if status == 'success':
                    print(f"\n{Colors.GREEN}✅ File transfer completed!{Colors.RESET}")
                    print(f"File '{Colors.BLUE}{filename}{Colors.RESET}' successfully received by {Colors.YELLOW}{receiver_name}{Colors.RESET}")
                else:
                    print(f"\n{Colors.RED}❌ File transfer failed!{Colors.RESET}")
                    print(f"File '{Colors.BLUE}{filename}{Colors.RESET}' transfer to {Colors.YELLOW}{receiver_name}{Colors.RESET} failed: {status}")
                
                # Clean up transfer state
                del self.active_file_transfers[transfer_id]
            
        except Exception as e:
            print(f"{Colors.RED}Error handling file received confirmation: {e}{Colors.RESET}")
    
    def _reassemble_file(self, transfer_id):
        """Reassemble file from chunks and save to disk"""
        try:
            if transfer_id not in self.receiving_files:
                return
            
            file_info = self.receiving_files[transfer_id]
            chunks = file_info['chunks']
            total_chunks = file_info['total_chunks']
            sender_addr = file_info['sender_addr']
            
            print(f"Debug: File info total_chunks: {total_chunks}")
            print(f"Debug: Available chunks: {list(chunks.keys())}")
            print(f"Debug: Chunk count: {len(chunks)}")
            
            # Get file offer info
            if transfer_id not in self.pending_file_offers:
                print(f"{Colors.RED}Error: File offer info not found for transfer {transfer_id}{Colors.RESET}")
                return
            
            offer_info = self.pending_file_offers[transfer_id]
            filename = offer_info['filename']
            
            # Reassemble file data
            file_data = b''
            print(f"Debug: Reassembling {total_chunks} chunks...")
            for i in range(total_chunks):
                if i in chunks:
                    try:
                        chunk_bytes = base64.b64decode(chunks[i])
                        file_data += chunk_bytes
                        print(f"Debug: Chunk {i} decoded: {len(chunk_bytes)} bytes")
                    except Exception as e:
                        print(f"{Colors.RED}Error decoding chunk {i}: {e}{Colors.RESET}")
                        self._send_file_received(transfer_id, sender_addr, 'decode_error')
                        return
                else:
                    print(f"{Colors.RED}Missing chunk {i}, cannot reassemble file{Colors.RESET}")
                    self._send_file_received(transfer_id, sender_addr, 'missing_chunks')
                    return
            
            print(f"Debug: Total reassembled file size: {len(file_data)} bytes")
            print(f"Debug: File data preview: {file_data[:50]}...")
            
            # Save file to downloads directory
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Handle filename conflicts
            file_path = os.path.join(downloads_dir, filename)
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(downloads_dir, new_filename)
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            print(f"\n{Colors.GREEN}📁 File saved successfully!{Colors.RESET}")
            print(f"Location: {Colors.BLUE}{file_path}{Colors.RESET}")
            print(f"Size: {self._format_file_size(len(file_data))}")
            
            # Send confirmation
            self._send_file_received(transfer_id, sender_addr, 'success')
            
            # Clean up
            del self.receiving_files[transfer_id]
            del self.pending_file_offers[transfer_id]
            
        except Exception as e:
            print(f"{Colors.RED}Error reassembling file: {e}{Colors.RESET}")
            if transfer_id in self.receiving_files:
                sender_addr = self.receiving_files[transfer_id]['sender_addr']
                self._send_file_received(transfer_id, sender_addr, 'write_error')
    
    def _send_file_received(self, transfer_id, addr, status):
        """Send FILE_RECEIVED confirmation message"""
        try:
            msg_dict = {
                'TYPE': 'FILE_RECEIVED',
                'transfer_id': transfer_id,
                'status': status,
                'receiver_name': self.peer_manager.get_self_info().get('name', 'Unknown')
            }
            
            self.network_manager.send_to_address(msg_dict, addr[0], addr[1])
            
        except Exception as e:
            print(f"{Colors.RED}Error sending file received confirmation: {e}{Colors.RESET}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def handle_file_accept(self, msg_dict, addr):
        """Handle FILE_ACCEPT message"""
        print(f"Debug: FILE_ACCEPT handler called from {addr}")
        print(f"Debug: Message content: {msg_dict}")
        
        try:
            transfer_id = msg_dict.get('transfer_id')
            receiver_name = msg_dict.get('receiver_name', f"Unknown@{addr[0]}")
            
            print(f"Debug: Received FILE_ACCEPT for transfer {transfer_id}")
            print(f"Debug: Active transfers: {list(self.active_file_transfers.keys())}")
            
            if transfer_id not in self.active_file_transfers:
                print(f"{Colors.RED}Error: Transfer {transfer_id} not found{Colors.RESET}")
                print(f"Debug: Available transfers: {list(self.active_file_transfers.keys())}")
                return
            
            transfer_info = self.active_file_transfers[transfer_id]
            filename = transfer_info['filename']
            file_path = transfer_info['file_path']
            
            print(f"\n{Colors.GREEN}✅ File offer accepted!{Colors.RESET}")
            print(f"Receiver: {Colors.YELLOW}{receiver_name}{Colors.RESET}")
            print(f"File: {Colors.BLUE}{filename}{Colors.RESET}")
            print(f"Starting file transfer...")
            
            # Update transfer status
            transfer_info['status'] = 'sending'
            transfer_info['receiver_name'] = receiver_name
            
            # Start sending file chunks
            self._send_file_chunks(transfer_id, file_path, addr)
            
        except Exception as e:
            print(f"{Colors.RED}Error handling file accept: {e}{Colors.RESET}")
    
    def handle_file_reject(self, msg_dict, addr):
        """Handle FILE_REJECT message"""
        try:
            transfer_id = msg_dict.get('transfer_id')
            receiver_name = msg_dict.get('receiver_name', f"Unknown@{addr[0]}")
            
            if transfer_id not in self.active_file_transfers:
                print(f"{Colors.RED}Error: Transfer {transfer_id} not found{Colors.RESET}")
                return
            
            transfer_info = self.active_file_transfers[transfer_id]
            filename = transfer_info['filename']
            
            print(f"\n{Colors.RED}❌ File offer rejected{Colors.RESET}")
            print(f"Receiver: {Colors.YELLOW}{receiver_name}{Colors.RESET}")
            print(f"File: {Colors.BLUE}{filename}{Colors.RESET}")
            
            # Clean up transfer
            del self.active_file_transfers[transfer_id]
            
        except Exception as e:
            print(f"{Colors.RED}Error handling file reject: {e}{Colors.RESET}")
    
    def _send_file_chunks(self, transfer_id, file_path, addr):
        """Send file as chunks to receiver"""
        try:
            chunk_size = 64 * 1024  # 64KB chunks
            
            print(f"Debug: Reading file from path: {file_path}")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            print(f"Debug: File data length: {len(file_data)} bytes")
            print(f"Debug: File data preview: {file_data[:50]}...")
            
            # Calculate chunks
            total_chunks = (len(file_data) + chunk_size - 1) // chunk_size
            
            print(f"Sending {total_chunks} chunks...")
            
            for chunk_num in range(total_chunks):
                start = chunk_num * chunk_size
                end = min(start + chunk_size, len(file_data))
                chunk_data = file_data[start:end]
                
                print(f"Debug: Chunk {chunk_num}: {len(chunk_data)} bytes")
                
                # Encode chunk as base64
                chunk_b64 = base64.b64encode(chunk_data).decode('utf-8')
                
                # Send chunk
                msg_dict = {
                    'TYPE': 'FILE_CHUNK',
                    'transfer_id': transfer_id,
                    'chunk_number': str(chunk_num),
                    'total_chunks': str(total_chunks),
                    'chunk_data': chunk_b64
                }
                
                self.network_manager.send_to_address(msg_dict, addr[0], addr[1])
                print(f"Sent chunk {chunk_num + 1}/{total_chunks}")
                
                # Small delay to avoid overwhelming receiver
                time.sleep(0.1)
            
            print(f"{Colors.GREEN}✅ File transfer completed!{Colors.RESET}")
            print(f"Waiting for confirmation from receiver...")
            
        except Exception as e:
            print(f"{Colors.RED}Error sending file chunks: {e}{Colors.RESET}")
            # Send error confirmation
            self._send_file_received(transfer_id, addr, 'send_error')
    
    def get_active_games(self):
        """Get list of active games"""
        return list(self.active_games.keys())
    
    def get_game_info(self, game_id):
        """Get information about a specific game"""
        return self.active_games.get(game_id)

            
    def handle_token_revocation(self, msg_dict, addr):
        """
        Handle token revocation message
        
        Args:
            msg_dict (dict): The message dictionary
            addr (tuple): Sender address (ip, port)
            
        Returns:
            bool: True if token was successfully revoked
        """
        user_id = msg_dict.get('USER_ID')
        token = msg_dict.get('TOKEN')
        
        # Log the revocation if in verbose mode
        if self.verbose_mode:
            print(f"\nRECV < From {addr[0]} | Type: REVOKE")
            print(f"TYPE: REVOKE")
            if user_id:
                print(f"USER_ID: {user_id}")
            if token:
                print(f"TOKEN: {token}")
        
        # Remove the peer from the known peers list
        if user_id and user_id in self.peer_manager.known_peers:
            if self.verbose_mode:
                print(f"[PEER LEFT] {user_id} has quit")
            
            # Remove from known peers
            if user_id in self.peer_manager.known_peers:
                del self.peer_manager.known_peers[user_id]
            
            # Add to revoked peers list to prevent rediscovery
            self.peer_manager.revoked_peers.add(user_id)
            
            # Remove from user profiles
            if user_id in self.peer_manager.user_profiles:
                del self.peer_manager.user_profiles[user_id]
            
            # Remove from followers and following lists
            if user_id in self.peer_manager.followers:
                self.peer_manager.followers.remove(user_id)
            if user_id in self.peer_manager.following:
                self.peer_manager.following.remove(user_id)
            
            # Trigger callback if set
            if self.peer_manager.on_peer_lost:
                self.peer_manager.on_peer_lost(user_id)
        
        # Revoke the token if provided
        if token:
            return self.peer_manager.revoke_token(token)
        
        return True
    
    def send_token_revocation(self, token, target_user_id=None):
        """
        Send token revocation message
        
        Args:
            token (str): The token to revoke
            target_user_id (str, optional): If specified, send only to this user
            
        Returns:
            bool: True if message was sent successfully
        """
        message = {
            'TYPE': 'REVOKE',
            'USER_ID': self.peer_manager.user_id,
            'TOKEN': token,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': secrets.token_hex(8)
        }
        
        # If target user specified, send only to them
        if target_user_id:
            peer_info = self.peer_manager.get_peer_info(target_user_id)
            if peer_info:
                return self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
            return False
            
        # Otherwise broadcast to all known peers
        return self.network_manager.broadcast_to_peers(message)
