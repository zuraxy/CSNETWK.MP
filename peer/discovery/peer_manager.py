#!/usr/bin/env python3
"""
Peer Discovery Module
Handles peer discovery, tracking, and management
"""
import time
import threading
import secrets
from peer.config.settings import DISCOVERY_INTERVAL, PEER_TIMEOUT

class PeerManager:
    """Manages peer discovery, tracking, and cleanup"""
    
    def __init__(self, discovery_interval=DISCOVERY_INTERVAL, peer_timeout=PEER_TIMEOUT):
        self.discovery_interval = discovery_interval
        self.peer_timeout = peer_timeout
        
        # Peer storage
        self.known_peers = {}  # user_id -> {'ip': str, 'port': int, 'last_seen': timestamp}
        self.user_profiles = {}  # user_id -> {'display_name': str, 'avatar': bool, 'avatar_type': str}
        
        # Direct message storage
        self.direct_messages = {}  # user_id -> [{'content': str, 'timestamp': int, 'from_user': str, 'to_user': str}]
        
        # Follow/Following functionality
        self.followers = set()  # Set of user_ids who follow me
        self.following = set()  # Set of user_ids I'm following
        
        # Group chat functionality
        self.groups = {}  # group_id -> {'name': str, 'creator': user_id, 'members': set(), 'created_at': timestamp}
        self.created_groups = set()  # Set of group_ids I've created
        
        # Post likes functionality
        self.liked_posts = set()  # Set of post_timestamps I've liked
        self.post_likes = {}  # post_timestamp -> set(user_ids who liked it)
        self.my_posts = {}  # timestamp -> {'content': str, 'ttl': int, 'created_at': int}
        self.received_posts = {}  # user_id -> {timestamp -> {'content': str, 'ttl': int, 'created_at': int}}
        
        # Discovery state
        self.user_id = ""
        self.network_manager = None
        self.running = False
        self.discovery_thread = None
        
        # Callbacks for events
        self.on_peer_discovered = None
        self.on_peer_lost = None
    
    def set_network_manager(self, network_manager):
        """Set the network manager for sending discovery messages"""
        self.network_manager = network_manager
    
    def set_user_id(self, user_id):
        """Set the current user ID"""
        self.user_id = user_id
    
    def start_discovery(self):
        """Start periodic peer discovery"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
        # Send initial announcement
        self.announce_presence()
    
    def stop_discovery(self):
        """Stop peer discovery"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=1)
    
    def _discovery_loop(self):
        """Periodic discovery and cleanup loop"""
        while self.running:
            time.sleep(self.discovery_interval)
            if self.running:
                self.announce_presence()
                self.cleanup_old_peers()
    
    def announce_presence(self):
        """Broadcast presence announcement"""
        if not self.network_manager or not self.user_id:
            return
        
        network_info = self.network_manager.get_network_info()
        announcement = {
            'TYPE': 'PEER_DISCOVERY',
            'USER_ID': self.user_id,
            'PORT': str(network_info['local_port']),
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        success = self.network_manager.broadcast_discovery(announcement)
        return success
    
    def handle_peer_discovery(self, msg_dict, addr):
        """Handle incoming peer discovery messages"""
        sender_id = msg_dict.get('USER_ID', '')
        if sender_id and sender_id != self.user_id:
            # Check if this is a new peer (not already known)
            is_new_peer = sender_id not in self.known_peers
            
            self.update_peer_info(sender_id, addr[0], msg_dict.get('PORT', addr[1]))
            
            # Send discovery response
            self.send_discovery_response(addr[0], int(msg_dict.get('PORT', addr[1])))
            
            # Only trigger callback for newly discovered peers
            if is_new_peer and self.on_peer_discovered:
                self.on_peer_discovered(sender_id)
    
    def send_discovery_response(self, target_ip, target_port):
        """Send discovery response to a specific peer"""
        if not self.network_manager:
            return
        
        network_info = self.network_manager.get_network_info()
        response = {
            'TYPE': 'PEER_DISCOVERY',
            'USER_ID': self.user_id,
            'PORT': str(network_info['local_port']),
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self._generate_message_id()
        }
        
        self.network_manager.send_to_address(response, target_ip, target_port)
    
    def update_peer_info(self, user_id, ip, port):
        """Update information about a known peer"""
        self.known_peers[user_id] = {
            'ip': ip,
            'port': int(port),
            'last_seen': time.time()
        }
    
    def update_user_profile(self, user_id, display_name=None, has_avatar=False, avatar_type=''):
        """Update stored user profile information"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        
        if display_name is not None:
            self.user_profiles[user_id]['display_name'] = display_name
        self.user_profiles[user_id]['avatar'] = has_avatar
        self.user_profiles[user_id]['avatar_type'] = avatar_type
    
    def get_display_name(self, user_id):
        """Get display name for a user, fallback to user_id if not available"""
        if user_id in self.user_profiles and self.user_profiles[user_id].get('display_name'):
            return self.user_profiles[user_id]['display_name']
        return user_id
    
    def get_avatar_info(self, user_id):
        """Get avatar information for a user"""
        if user_id in self.user_profiles and self.user_profiles[user_id].get('avatar'):
            avatar_type = self.user_profiles[user_id].get('avatar_type', '')
            if avatar_type:
                return f"[AVATAR]({avatar_type})"
            return "[AVATAR]"
        return ""
    
    def cleanup_old_peers(self):
        """Remove peers that haven't been seen recently"""
        current_time = time.time()
        peers_to_remove = []
        
        for user_id, peer_info in self.known_peers.items():
            if current_time - peer_info['last_seen'] > self.peer_timeout:
                peers_to_remove.append(user_id)
        
        for user_id in peers_to_remove:
            del self.known_peers[user_id]
            if user_id in self.user_profiles:
                del self.user_profiles[user_id]
            
            # Remove from followers and following lists
            if user_id in self.followers:
                self.followers.remove(user_id)
            if user_id in self.following:
                self.following.remove(user_id)
            
            # Trigger callback if set
            if self.on_peer_lost:
                self.on_peer_lost(user_id)
    
    def get_peer_list(self):
        """Get list of known peers"""
        return list(self.known_peers.keys())
    
    def get_peer_info(self, user_id):
        """Get information about a specific peer"""
        return self.known_peers.get(user_id)
    
    def get_all_peers(self):
        """Get all peer information"""
        return self.known_peers.copy()
    
    def is_peer_known(self, user_id):
        """Check if a peer is known"""
        return user_id in self.known_peers
    
    def follow_peer(self, user_id):
        """Add a peer to your following list"""
        if self.is_peer_known(user_id) and user_id != self.user_id:
            self.following.add(user_id)
            return True
        return False
    
    def unfollow_peer(self, user_id):
        """Remove a peer from your following list"""
        if user_id in self.following:
            self.following.remove(user_id)
            return True
        return False
    
    def add_follower(self, user_id):
        """Add a peer to your followers list"""
        if self.is_peer_known(user_id) and user_id != self.user_id:
            self.followers.add(user_id)
            return True
        return False
    
    def remove_follower(self, user_id):
        """Remove a peer from your followers list"""
        if user_id in self.followers:
            self.followers.remove(user_id)
            return True
        return False
    
    def get_followers(self):
        """Get list of followers"""
        return list(self.followers)
    
    def get_following(self):
        """Get list of peers you're following"""
        return list(self.following)
    
    def is_following(self, user_id):
        """Check if you are following a peer"""
        return user_id in self.following
    
    def is_follower(self, user_id):
        """Check if a peer is following you"""
        return user_id in self.followers
    
    # Group management methods
    def add_group(self, group_id, group_name, creator_id, members, timestamp):
        """Add a group the user belongs to"""
        if group_id not in self.groups:
            self.groups[group_id] = {
                'name': group_name,
                'creator': creator_id,
                'members': set(),
                'created_at': timestamp
            }
            
        # Update group info
        self.groups[group_id]['name'] = group_name
        
        # Update member list
        self.groups[group_id]['members'] = members
        
        # Check if user is creator
        if creator_id == self.user_id:
            self.created_groups.add(group_id)
            
        return True
        
    def update_group(self, group_id, updater_id, add_members=None, remove_members=None):
        """Update group membership"""
        # Verify group exists
        if group_id not in self.groups:
            return False
            
        # Verify updater is creator (only creator can update)
        if self.groups[group_id]['creator'] != updater_id:
            return False
            
        # Add members
        if add_members:
            for member in add_members:
                self.groups[group_id]['members'].add(member)
                
        # Remove members
        if remove_members:
            for member in remove_members:
                if member in self.groups[group_id]['members']:
                    self.groups[group_id]['members'].remove(member)
                    
        return True
    
    def join_group(self, group_id, group_name, creator, members=None, created_at=None):
        """Join a group created by someone else"""
        if group_id in self.groups:
            # Group already exists, just make sure we're in it
            if self.user_id not in self.groups[group_id]['members']:
                self.groups[group_id]['members'].append(self.user_id)
            self.my_groups.add(group_id)
            return True, "Joined existing group"
        
        # Create group entry
        if not members:
            members = [creator, self.user_id]
        elif self.user_id not in members:
            members.append(self.user_id)
            
        self.groups[group_id] = {
            'name': group_name,
            'creator': creator,
            'members': members,
            'created_at': created_at or time.time()
        }
        
        # Add to my groups
        self.my_groups.add(group_id)
        
        return True, "Joined new group"
    
    def leave_group(self, group_id):
        """Leave a group"""
        if group_id not in self.groups:
            return False, "Group not found"
        
        # If you're the creator, you can't leave (must delete instead)
        if self.groups[group_id]['creator'] == self.user_id:
            return False, "As the creator, you cannot leave. Delete the group instead."
        
        # Remove from members list
        if self.user_id in self.groups[group_id]['members']:
            self.groups[group_id]['members'].remove(self.user_id)
        
        return True, "Left group successfully"
    
    def get_my_groups(self):
        """Get groups the user is a member of"""
        return [group_id for group_id, group in self.groups.items() 
                if self.user_id in group['members']]
    
    def is_in_group(self, group_id):
        """Check if user is in a group"""
        return (group_id in self.groups and 
                self.user_id in self.groups[group_id]['members'])
    
    def delete_group(self, group_id):
        """Delete a group (creator only)"""
        if group_id not in self.groups:
            return False, "Group not found"
        
        # Only creator can delete
        if self.groups[group_id]['creator'] != self.user_id:
            return False, "Only the group creator can delete the group"
        
        # Delete group
        del self.groups[group_id]
        
        # Remove from created groups
        if group_id in self.created_groups:
            self.created_groups.remove(group_id)
        
        return True, "Group deleted successfully"
    
    def get_group(self, group_id):
        """Get group information"""
        return self.groups.get(group_id)
    
    def get_group_name(self, group_id):
        """Get the name of a group"""
        group = self.groups.get(group_id)
        return group['name'] if group else None
    
    def get_group_members(self, group_id):
        """Get list of members in a group"""
        group = self.groups.get(group_id)
        return group['members'] if group else []
    
    def get_group_creator(self, group_id):
        """Get the creator of a group"""
        group = self.groups.get(group_id)
        return group['creator'] if group else None
    
    def is_group_member(self, group_id, user_id=None):
        """Check if a user is a member of a group"""
        if user_id is None:
            user_id = self.user_id
            
        group = self.groups.get(group_id)
        return group and user_id in group['members']
    
    def is_group_creator(self, group_id, user_id=None):
        """Check if a user is the creator of a group"""
        if user_id is None:
            user_id = self.user_id
            
        group = self.groups.get(group_id)
        return group and group['creator'] == user_id
    
    def get_my_groups(self):
        """Get list of groups the user is a member of"""
        return [group_id for group_id, group in self.groups.items() 
                if self.user_id in group['members']]
    
    def is_in_group(self, group_id):
        """Check if user is in a group"""
        return (group_id in self.groups and 
                self.user_id in self.groups[group_id]['members'])
    
    def get_all_groups(self):
        """Get all known groups"""
        return self.groups.copy()
    
    def _generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)
        
    def store_direct_message(self, from_user, to_user, content, timestamp):
        """Store a direct message"""
        # Convert timestamp to int if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = int(timestamp)
            except ValueError:
                timestamp = int(time.time())
        
        # Create message object
        dm = {
            'from_user': from_user,
            'to_user': to_user,
            'content': content,
            'timestamp': timestamp
        }
        
        # Store based on the other party (whether sent or received)
        other_party = from_user if to_user == self.user_id else to_user
        
        if other_party not in self.direct_messages:
            self.direct_messages[other_party] = []
        
        self.direct_messages[other_party].append(dm)
        
    def get_direct_messages(self, peer_id):
        """Get all direct messages exchanged with a specific peer"""
        if peer_id not in self.direct_messages:
            return []
        
        # Sort messages by timestamp
        messages = sorted(self.direct_messages[peer_id], key=lambda x: x['timestamp'])
        return messages
        
    # Post likes management
    def add_post(self, timestamp, content, ttl=3600):
        """Track a post created by the user
        
        Args:
            timestamp (str): The timestamp when the post was created
            content (str): The content of the post
            ttl (int): Time To Live in seconds
            
        Returns:
            bool: True if post was added successfully
        """
        created_at = int(timestamp)
        self.my_posts[timestamp] = {
            'content': content,
            'ttl': int(ttl),
            'created_at': created_at
        }
        return True
        
    def add_received_post(self, user_id, timestamp, content, ttl=3600):
        """Track a post received from another user
        
        Args:
            user_id (str): The ID of the user who sent the post
            timestamp (str): The timestamp when the post was created
            content (str): The content of the post
            ttl (int): Time To Live in seconds
            
        Returns:
            bool: True if post was added successfully
        """
        if user_id not in self.received_posts:
            self.received_posts[user_id] = {}
            
        created_at = int(timestamp)
        self.received_posts[user_id][timestamp] = {
            'content': content,
            'ttl': int(ttl),
            'created_at': created_at
        }
        return True
        
    def get_user_posts(self, user_id):
        """Get posts from a specific user, filtering out expired posts
        
        Args:
            user_id (str): The ID of the user whose posts to get
            
        Returns:
            dict: Dictionary of timestamp -> post data
        """
        # Get current time
        current_time = int(time.time())
        
        if user_id == self.user_id:
            # Filter out expired posts
            valid_posts = {}
            for timestamp, post_data in self.my_posts.items():
                created_at = post_data['created_at']
                ttl = post_data['ttl']
                
                # Check if post is still valid
                if created_at + ttl > current_time:
                    valid_posts[timestamp] = post_data
                    
            return valid_posts
        else:
            if user_id not in self.received_posts:
                return {}
                
            # Filter out expired posts
            valid_posts = {}
            for timestamp, post_data in self.received_posts[user_id].items():
                created_at = post_data['created_at']
                ttl = post_data['ttl']
                
                # Check if post is still valid
                if created_at + ttl > current_time:
                    valid_posts[timestamp] = post_data
                    
            return valid_posts
        
    def like_post(self, post_author, post_timestamp):
        """Like a post"""
        # Track that the current user has liked this post
        like_key = f"{post_author}:{post_timestamp}"
        self.liked_posts.add(like_key)
        
        # Add the like to the post
        if post_timestamp not in self.post_likes:
            self.post_likes[post_timestamp] = set()
        self.post_likes[post_timestamp].add(self.user_id)
        
        return True
        
    def unlike_post(self, post_author, post_timestamp):
        """Unlike a post"""
        # Remove from liked posts
        like_key = f"{post_author}:{post_timestamp}"
        if like_key in self.liked_posts:
            self.liked_posts.remove(like_key)
        
        # Remove the like from the post
        if post_timestamp in self.post_likes and self.user_id in self.post_likes[post_timestamp]:
            self.post_likes[post_timestamp].remove(self.user_id)
            
        return True
        
    def has_liked_post(self, post_author, post_timestamp):
        """Check if the user has liked a post"""
        like_key = f"{post_author}:{post_timestamp}"
        return like_key in self.liked_posts
        
    def get_post_likes(self, post_timestamp):
        """Get users who liked a post"""
        return self.post_likes.get(post_timestamp, set())
        
    def get_post_likes_count(self, post_timestamp):
        """Get the number of likes for a post"""
        return len(self.post_likes.get(post_timestamp, set()))
        
    def get_post_content(self, post_timestamp):
        """Get the content of a post
        
        Args:
            post_timestamp (str): The timestamp of the post
            
        Returns:
            str: The content of the post, or empty string if not found or expired
        """
        # Check if post exists
        post = self.my_posts.get(post_timestamp)
        if not post:
            return ""
            
        # Check if post is expired
        current_time = int(time.time())
        created_at = post['created_at']
        ttl = post['ttl']
        
        if created_at + ttl <= current_time:
            return ""  # Post expired
            
        return post['content']