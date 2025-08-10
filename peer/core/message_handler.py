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
        self.network_manager.register_message_handler('FOLLOW', self.handle_follow_request)
        self.network_manager.register_message_handler('UNFOLLOW', self.handle_unfollow_request)
        self.network_manager.register_message_handler('FOLLOW_RESPONSE', self.handle_follow_response)
        self.network_manager.register_message_handler('UNFOLLOW_RESPONSE', self.handle_unfollow_response)
        
        # Group chat message handlers
        self.network_manager.register_message_handler('GROUP_CREATE', self.handle_group_create)
        self.network_manager.register_message_handler('GROUP_UPDATE', self.handle_group_update)
        self.network_manager.register_message_handler('GROUP_MESSAGE', self.handle_group_message)
    
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
        
        # Prepare message
        message = {
            'TYPE': 'GROUP_MESSAGE',
            'FROM': self.peer_manager.user_id,
            'GROUP_ID': group_id,
            'CONTENT': content,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
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
        
        # Verify this is a valid group and we're a member
        if not self.peer_manager.is_in_group(group_id):
            # Not a member, ignore the message
            return
            
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
        timestamp = msg_dict.get('TIMESTAMP', None)
        token = msg_dict.get('TOKEN', '')
        msg_type = msg_dict.get('TYPE', 'GROUP_MESSAGE')
        message_id = msg_dict.get('MESSAGE_ID', '')
        
        # Check if we know about this group
        group = self.peer_manager.get_group(group_id)
        if not group:
            return
            
        # Check if we are a member of this group
        if not self.peer_manager.is_group_member(group_id):
            return
            
        # Check if sender is a member of the group
        if from_user not in group['members']:
            if self.verbose_mode:
                print(f"\n[ERROR] Group message from non-member {from_user} rejected")
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
            print(f"FROM: {from_user}")
            print(f"GROUP_ID: {group_id}")
            print(f"CONTENT: {content}")
            print(f"TIMESTAMP: {timestamp}")
            print(f"TOKEN: {token}")
            print(f"MESSAGE_ID: {message_id}")
        else:
            display_name = self.peer_manager.get_display_name(from_user)
            avatar_info = self.peer_manager.get_avatar_info(from_user)
            print(f"\n[{group['name']}] {display_name}{avatar_info}: {content}")
