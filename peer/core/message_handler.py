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
import threading

# For TTL
from peer.config.settings import (
    DEFAULT_POST_TTL, TTL_CLEANUP_INTERVAL
)

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
        
        # Add message cache with TTL support
        self.message_cache = {}  # message_id -> (message_dict, expiry_time)
        
        # Start TTL cleanup thread
        self.ttl_cleanup_thread = threading.Thread(target=self._ttl_cleanup_loop)
        self.ttl_cleanup_thread.daemon = True
        self.ttl_cleanup_thread.start()
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all message type handlers"""
        self.network_manager.register_message_handler('PEER_DISCOVERY', self.handle_peer_discovery)
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
        ttl = msg_dict.get('TTL', str(DEFAULT_PROFILE_TTL))
        message_id = msg_dict.get('MESSAGE_ID', '')
        msg_type = msg_dict.get('TYPE', 'PROFILE')

        # Check TTL
        if not self._is_message_valid(timestamp, ttl):
            if self.verbose_mode:
                print(f"\n[EXPIRED] PROFILE from {user_id} has expired - TTL: {ttl}")
            return

        # Update profile storage
        self.peer_manager.update_user_profile(user_id, display_name, has_avatar, avatar_type)

        # Store valid message with expiry
        if message_id:
            self._store_message(message_id, msg_dict)

        if self.verbose_mode:
            # Format timestamp
            if timestamp:
                try:
                    ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    expiry_time = datetime.datetime.fromtimestamp(int(timestamp) + int(ttl)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    ts_str = str(timestamp)
                    expiry_time = str(timestamp)
            else:
                ts_str = "N/A"
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
            print(f"TYPE: {msg_type}")
            print(f"USER_ID: {user_id}")
            print(f"DISPLAY_NAME: {display_name}")
            print(f"STATUS: {status}")
            print(f"TTL: {ttl} (Expires: {expiry_time})")
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
        
        # Check TTL
        if not self._is_message_valid(timestamp, ttl):
            if self.verbose_mode:
                print(f"\n[EXPIRED] POST from {user_id} has expired - TTL: {ttl}")
            return
        
        # Only process messages from users you follow (if not in verbose mode)
        if not self.verbose_mode and not self.peer_manager.is_following(user_id):
            if self.verbose_mode:
                print(f"\n[FILTERED] POST from {user_id} ignored - not following this user")
            return
        
        # Store valid message with expiry
        if message_id:
            self._store_message(message_id, msg_dict)

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
                    expiry_time = datetime.datetime.fromtimestamp(int(timestamp) + int(ttl)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    ts_str = str(timestamp)
                    expiry_time = str(timestamp)
            else:
                ts_str = "N/A"
            print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
            print(f"TYPE: {msg_type}")
            print(f"USER_ID: {user_id}")
            print(f"CONTENT: {content}")
            print(f"TTL: {ttl} (Expires: {expiry_time})")
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
        ttl = msg_dict.get('TTL', str(DEFAULT_DM_TTL))
        msg_type = msg_dict.get('TYPE', 'DM')
        message_id = msg_dict.get('MESSAGE_ID', '')
        token = msg_dict.get('TOKEN', '')

        # Check TTL
        if not self._is_message_valid(timestamp, ttl):
            if self.verbose_mode:
                print(f"\n[EXPIRED] DM from {from_user} has expired - TTL: {ttl}")
            return

        # Only display if this message is for us
        if to_user == self.peer_manager.user_id:
            # Store valid message with expiry
            if message_id:
                self._store_message(message_id, msg_dict)

            if self.verbose_mode:
                # Format timestamp
                if timestamp:
                    try:
                        ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                        expiry_time = datetime.datetime.fromtimestamp(int(timestamp) + int(ttl)).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = str(timestamp)
                        expiry_time = str(timestamp)
                else:
                    ts_str = "N/A"
                print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: {msg_type}")
                print(f"TYPE: {msg_type}")
                print(f"FROM: {from_user}")
                print(f"TO: {to_user}")
                print(f"CONTENT: {content}")
                print(f"TIMESTAMP: {timestamp}")
                print(f"TTL: {ttl} (Expires: {expiry_time})")
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
        timestamp = int(time.time())
        message_id = self._generate_message_id()

        message = {
            'TYPE': 'POST',
            'USER_ID': self.peer_manager.user_id,
            'CONTENT': content,
            'TIMESTAMP': str(timestamp),
            'TTL': str(DEFAULT_POST_TTL),  
            'MESSAGE_ID': message_id
        }

        # Store the message locally with TTL
        self._store_message(message_id, message)

        encoded_msg = Protocol.encode_message(message)
        
        # REMOVE THIS LINE: self.network_manager.broadcast_message(encoded_msg)
        
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
        timestamp = int(time.time())
        message_id = self._generate_message_id()

        # Create the follow request message
        message = {
            'TYPE': 'FOLLOW',
            'FROM': self.peer_manager.user_id,
            'TO': target_user_id,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': str(timestamp)
        }

        # Check if target peer exists
        if target_user_id in self.peer_manager.known_peers:
            peer_info = self.peer_manager.known_peers[target_user_id]
            # Use send_to_address instead of broadcast_message
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

    # ==================== HELPER METHODS ====================

    # TTL Implementation
    def _is_message_valid(self, timestamp, ttl):
        """Check if a message is still valid based on its timestamp and TTL"""
        if not timestamp or not ttl:
            return False
            
        try:
            creation_time = int(timestamp)
            ttl_seconds = int(ttl)
            current_time = int(time.time())
            
            # Message is valid if: creation_time + ttl_seconds > current_time
            return (creation_time + ttl_seconds) > current_time
        except ValueError:
            # If parsing fails, consider message invalid
            return False
        
    def _store_message(self, message_id, msg_dict):
        """Store message with TTL-based expiration"""
        msg_type = msg_dict.get('TYPE', '')
        timestamp = int(msg_dict.get('TIMESTAMP', time.time()))
        
        if msg_type == 'POST':
            # Only POST messages should use TTL field as per spec
            ttl = int(msg_dict.get('TTL', DEFAULT_POST_TTL))
            expiry_time = timestamp + ttl
        else:
            # For non-POST messages, don't use TTL field
            # Either store indefinitely or use a default value for implementation
            # purposes (not a protocol requirement)
            expiry_time = float('inf')  # Store indefinitely
            # Alternative: use a default storage time for memory management
            # expiry_time = timestamp + DEFAULT_STORAGE_TIME
        
        self.message_cache[message_id] = (msg_dict, expiry_time)

    def _ttl_cleanup_loop(self):
        """Periodically clean up expired messages"""
        while True:
            try:
                time.sleep(TTL_CLEANUP_INTERVAL)  # Check every minute by default
                
                current_time = int(time.time())
                expired_ids = [mid for mid, (_, expiry) in self.message_cache.items() 
                                if expiry <= current_time]
                
                for mid in expired_ids:
                    del self.message_cache[mid]
                    
                if expired_ids and self.verbose_mode:
                    print(f"\n[TTL] Cleaned up {len(expired_ids)} expired messages")
                    
            except Exception as e:
                if self.verbose_mode:
                    print(f"\n[ERROR] TTL cleanup error: {e}")
