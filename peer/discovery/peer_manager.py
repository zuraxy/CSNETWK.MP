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
        
        # Follow/Following functionality
        self.followers = set()  # Set of user_ids who follow me
        self.following = set()  # Set of user_ids I'm following
        
        # Group chat functionality
        self.groups = {}  # group_id -> {'name': str, 'creator': user_id, 'members': set(), 'created_at': timestamp}
        self.created_groups = set()  # Set of group_ids I've created
        
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
    
    def find_peer_by_handle(self, handle):
        """Find a peer by handle (user@ip format)"""
        try:
            if '@' not in handle:
                return None
            
            user_part, ip_part = handle.split('@', 1)
            
            # Look for exact match in known peers
            for user_id, peer_info in self.known_peers.items():
                if peer_info['ip'] == ip_part:
                    # If user part matches or is empty, return this peer
                    if not user_part or user_id.startswith(user_part):
                        return {
                            'user_id': user_id,
                            'name': self.get_display_name(user_id),
                            'addr': (peer_info['ip'], peer_info['port'])
                        }
            
            # If no known peer found, try to create a basic peer info
            # This allows sending to peers not yet discovered
            try:
                # Use default port if not specified
                if ':' in ip_part:
                    ip, port = ip_part.split(':', 1)
                    port = int(port)
                else:
                    ip = ip_part
                    port = 12345  # Default port
                
                return {
                    'user_id': handle,
                    'name': handle,
                    'addr': (ip, port)
                }
            except ValueError:
                return None
                
        except Exception:
            return None
    
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