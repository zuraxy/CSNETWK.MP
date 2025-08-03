import time
import logging
from typing import Dict, List, Set, Optional, Tuple, Any

logger = logging.getLogger('lsnp.peer')

class Peer:
    """
    Manages the local peer's state and tracks other peers in the network.
    Responsible for maintaining peer relationships, post history, and group membership.
    """
    
    def __init__(self, username: str, ip_address: str, status: str = "Hello from LSNP!", port: int = 50999):
        """Initialize a new peer"""
        self.username = username
        self.ip_address = ip_address
        self.port = port
        self.user_id = f"{username}@{ip_address}"
        self.display_name = username
        self.status = status
        self.avatar_path = None
        self.has_avatar = False
        self.avatar_type = None
        
        # Track other peers
        self.known_peers = {}  # user_id -> {ip, port, display_name, status, last_seen, has_avatar, avatar_type}
        
        # Social relationships
        self.following = set()  # Set of user_ids this peer follows
        self.followers = set()  # Set of user_ids following this peer
        
        # Message storage
        self.posts = {}  # message_id -> {user_id, content, timestamp}
        self.dms_received = {}  # message_id -> {from, content, timestamp}
        self.dms_sent = {}  # message_id -> {to, content, timestamp}
        
        # Group membership
        self.groups = {}  # group_id -> {name, members, creator}
        
        # Token revocation list
        self.revoked_tokens = set()
        
        # File transfer tracking
        self.pending_files = {}  # file_id -> {from, filename, size, type, chunks_received, total_chunks}
        self.file_offers = {}  # file_id -> {from, filename, size, type, description}
        
        # Game state
        self.active_games = {}  # game_id -> {opponent, board, turn, symbol}
        
        # Last broadcast times
        self.last_ping_time = 0
        self.last_profile_time = 0
        
        logger.info(f"Local peer initialized: {self.user_id}")
    
    def update_profile(self, display_name: Optional[str] = None, status: Optional[str] = None, 
                      avatar_path: Optional[str] = None):
        """Update the local peer's profile information"""
        if display_name:
            self.display_name = display_name
        if status:
            self.status = status
        if avatar_path:
            self.avatar_path = avatar_path
            self.has_avatar = True
        logger.debug(f"Profile updated: {self.display_name}, {self.status}, has_avatar={self.has_avatar}")
    
    def update_peer(self, user_id: str, ip: str = None, port: int = None, 
                   display_name: str = None, status: str = None, 
                   has_avatar: bool = None, avatar_type: str = None):
        """Update information about a peer"""
        # Create entry if it doesn't exist
        if user_id not in self.known_peers:
            self.known_peers[user_id] = {
                'ip': None, 
                'port': None,
                'display_name': None,
                'status': None,
                'last_seen': time.time(),
                'has_avatar': False,
                'avatar_type': None
            }
        
        # Update peer information
        if ip:
            self.known_peers[user_id]['ip'] = ip
        if port:
            self.known_peers[user_id]['port'] = port
        if display_name:
            self.known_peers[user_id]['display_name'] = display_name
        if status:
            self.known_peers[user_id]['status'] = status
        if has_avatar is not None:
            self.known_peers[user_id]['has_avatar'] = has_avatar
        if avatar_type:
            self.known_peers[user_id]['avatar_type'] = avatar_type
            
        # Update last seen timestamp
        self.known_peers[user_id]['last_seen'] = time.time()
        
        logger.debug(f"Updated peer info: {user_id}")
        return self.known_peers[user_id]
    
    def add_or_update_from_ping(self, user_id: str, ip: str, port: int = 50999) -> None:
        """
        Update peer information from a PING message.
        
        Args:
            user_id: User ID from the PING message
            ip: IP address the PING came from
            port: Port the PING came from (default: 50999)
        """
        parts = user_id.split('@')
        if len(parts) == 2:
            username = parts[0]
            self.update_peer(user_id, ip=ip, port=port)
            logger.debug(f"Updated peer from PING: {user_id} at {ip}:{port}")
        else:
            logger.warning(f"Invalid user_id format in PING: {user_id}")
    
    def add_or_update_from_profile(self, profile_data: dict, sender_addr: Tuple[str, int]) -> None:
        """
        Update peer information from a PROFILE message.
        
        Args:
            profile_data: Decoded PROFILE message dictionary
            sender_addr: Tuple of (ip, port) the message came from
        """
        user_id = profile_data.get('USER_ID')
        if not user_id:
            logger.warning("Received PROFILE without USER_ID")
            return
            
        sender_ip, sender_port = sender_addr
        display_name = profile_data.get('DISPLAY_NAME')
        status = profile_data.get('STATUS')
        has_avatar = 'AVATAR_DATA' in profile_data
        avatar_type = profile_data.get('AVATAR_TYPE')
        
        # Update peer info
        self.update_peer(
            user_id=user_id, 
            ip=sender_ip,
            port=sender_port,
            display_name=display_name,
            status=status,
            has_avatar=has_avatar,
            avatar_type=avatar_type
        )
        
        # Store avatar data if present
        if has_avatar and 'AVATAR_DATA' in profile_data:
            self.store_avatar_data(user_id, profile_data['AVATAR_DATA'], avatar_type)
            
        logger.info(f"Updated peer from PROFILE: {display_name or user_id}")
    
    def store_avatar_data(self, user_id: str, avatar_data: str, avatar_type: str) -> bool:
        """
        Store avatar data for a peer.
        
        Args:
            user_id: User ID to store avatar for
            avatar_data: Base64-encoded avatar data
            avatar_type: MIME type of the avatar
            
        Returns:
            Success status
        """
        if user_id not in self.known_peers:
            logger.warning(f"Cannot store avatar for unknown peer: {user_id}")
            return False
            
        # In a real implementation, you would store this to a file or database
        # For now, just mark that we have the avatar and store the data in memory
        self.known_peers[user_id]['has_avatar'] = True
        self.known_peers[user_id]['avatar_type'] = avatar_type
        self.known_peers[user_id]['avatar_data'] = avatar_data
        
        logger.info(f"Stored avatar for {user_id}")
        return True
    
    def record_broadcast_time(self, message_type: str) -> None:
        """
        Record the time a broadcast message was sent.
        
        Args:
            message_type: Type of message sent (PING or PROFILE)
        """
        current_time = time.time()
        
        if message_type == 'PING':
            self.last_ping_time = current_time
        elif message_type == 'PROFILE':
            self.last_profile_time = current_time
    
    def should_send_profile(self, interval: int = 300) -> bool:
        """
        Determine if a PROFILE should be sent based on time since last broadcast.
        
        Args:
            interval: Broadcast interval in seconds (default: 300)
            
        Returns:
            True if PROFILE should be sent, False if PING is sufficient
        """
        current_time = time.time()
        # Send PROFILE if we haven't sent one in the specified interval
        return (current_time - self.last_profile_time) >= interval
    
    def get_peer_address(self, user_id: str) -> tuple:
        """Get IP and port for a peer"""
        if user_id not in self.known_peers:
            return None, None
            
        return self.known_peers[user_id]['ip'], self.known_peers[user_id]['port']
    
    def follow_user(self, user_id: str) -> bool:
        """Follow a user"""
        if user_id not in self.known_peers:
            logger.warning(f"Cannot follow unknown user: {user_id}")
            return False
            
        self.following.add(user_id)
        logger.info(f"Now following: {user_id}")
        return True
    
    def unfollow_user(self, user_id: str) -> bool:
        """Unfollow a user"""
        if user_id in self.following:
            self.following.remove(user_id)
            logger.info(f"Unfollowed: {user_id}")
            return True
        return False
    
    def add_follower(self, user_id: str) -> bool:
        """Add a follower"""
        if user_id not in self.known_peers:
            logger.warning(f"Cannot add unknown user as follower: {user_id}")
            return False
            
        self.followers.add(user_id)
        logger.info(f"New follower: {user_id}")
        return True
    
    def remove_follower(self, user_id: str) -> bool:
        """Remove a follower"""
        if user_id in self.followers:
            self.followers.remove(user_id)
            logger.info(f"Removed follower: {user_id}")
            return True
        return False
    
    def add_post(self, user_id: str, message_id: str, content: str, timestamp: int) -> bool:
        """Store a post from another user"""
        # Only store posts from users we follow
        if user_id != self.user_id and user_id not in self.following:
            logger.debug(f"Ignoring post from non-followed user: {user_id}")
            return False
            
        self.posts[message_id] = {
            'user_id': user_id,
            'content': content,
            'timestamp': timestamp
        }
        logger.debug(f"Stored post {message_id} from {user_id}")
        return True
    
    def add_received_dm(self, message_id: str, from_user: str, content: str, timestamp: int) -> bool:
        """Store a received direct message"""
        self.dms_received[message_id] = {
            'from': from_user,
            'content': content,
            'timestamp': timestamp
        }
        logger.debug(f"Stored received DM {message_id} from {from_user}")
        return True
    
    def add_sent_dm(self, message_id: str, to_user: str, content: str, timestamp: int) -> bool:
        """Store a sent direct message"""
        self.dms_sent[message_id] = {
            'to': to_user,
            'content': content,
            'timestamp': timestamp
        }
        logger.debug(f"Stored sent DM {message_id} to {to_user}")
        return True
    
    def is_following(self, user_id: str) -> bool:
        """Check if the local peer follows a user"""
        return user_id in self.following
    
    def is_followed_by(self, user_id: str) -> bool:
        """Check if the local peer is followed by a user"""
        return user_id in self.followers
    
    def revoke_token(self, token: str) -> None:
        """Add a token to the revocation list"""
        self.revoked_tokens.add(token)
        logger.info(f"Token revoked: {token}")
        
        # Cleanup old revoked tokens if list gets too large
        if len(self.revoked_tokens) > 100:
            # This is a simple approach - in a real implementation, 
            # we would want to expire old tokens based on their expiry time
            self.revoked_tokens = set(list(self.revoked_tokens)[-100:])
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked"""
        return token in self.revoked_tokens
    
    def get_known_peers(self) -> dict:
        """Get all known peers"""
        return self.known_peers
    
    def cleanup_inactive_peers(self, max_age_seconds: int = 1800) -> int:
        """Remove peers that haven't been seen recently"""
        current_time = time.time()
        inactive_peers = []
        
        for user_id, peer_info in self.known_peers.items():
            if current_time - peer_info['last_seen'] > max_age_seconds:
                inactive_peers.append(user_id)
        
        # Remove inactive peers
        for user_id in inactive_peers:
            del self.known_peers[user_id]
            if user_id in self.following:
                self.following.remove(user_id)
            if user_id in self.followers:
                self.followers.remove(user_id)
                
        if inactive_peers:
            logger.info(f"Removed {len(inactive_peers)} inactive peers")
            
        return len(inactive_peers)
    
    def create_group(self, group_id: str, group_name: str, members: List[str]) -> bool:
        """Create a new group"""
        if group_id in self.groups:
            logger.warning(f"Group already exists: {group_id}")
            return False
            
        self.groups[group_id] = {
            'name': group_name,
            'members': set(members),
            'creator': self.user_id,
            'created': int(time.time())
        }
        logger.info(f"Created group: {group_name} ({group_id}) with {len(members)} members")
        return True
    
    def update_group(self, group_id: str, add_members: List[str] = None, remove_members: List[str] = None) -> bool:
        """Update group membership"""
        if group_id not in self.groups:
            logger.warning(f"Cannot update unknown group: {group_id}")
            return False
            
        group = self.groups[group_id]
        
        # Add new members
        if add_members:
            for member in add_members:
                group['members'].add(member)
                
        # Remove members
        if remove_members:
            for member in remove_members:
                if member in group['members']:
                    group['members'].remove(member)
        
        logger.info(f"Updated group {group_id}, now has {len(group['members'])} members")
        return True
    
    def get_group_members(self, group_id: str) -> Set[str]:
        """Get members of a group"""
        if group_id not in self.groups:
            return set()
        return self.groups[group_id]['members'].copy()
    
    def is_group_member(self, group_id: str, user_id: str) -> bool:
        """Check if a user is a member of a group"""
        if group_id not in self.groups:
            return False
        return user_id in self.groups[group_id]['members']
    
    def get_user_groups(self) -> List[str]:
        """Get all groups that the user is a member of"""
        return [group_id for group_id, group in self.groups.items() 
                if self.user_id in group['members']]
    
    def get_display_name(self, user_id: str) -> str:
        """Get display name for a user, fallback to user_id if not available"""
        if user_id == self.user_id:
            return self.display_name
            
        if user_id in self.known_peers and self.known_peers[user_id]['display_name']:
            return self.known_peers[user_id]['display_name']
            
        return user_id
    
    def process_file_offer(self, file_id: str, from_user: str, filename: str, 
                         filesize: int, filetype: str, description: str = "") -> bool:
        """Process a file transfer offer"""
        self.file_offers[file_id] = {
            'from': from_user,
            'filename': filename,
            'size': filesize,
            'type': filetype,
            'description': description,
            'offered_at': time.time()
        }
        logger.info(f"Received file offer: {filename} ({filesize} bytes) from {from_user}")
        return True
    
    def accept_file_offer(self, file_id: str) -> bool:
        """Accept a file transfer offer"""
        if file_id not in self.file_offers:
            logger.warning(f"Unknown file offer: {file_id}")
            return False
            
        # Move from offers to pending
        offer = self.file_offers.pop(file_id)
        self.pending_files[file_id] = {
            'from': offer['from'],
            'filename': offer['filename'],
            'size': offer['size'],
            'type': offer['type'],
            'chunks_received': {},
            'total_chunks': None,
            'started_at': time.time()
        }
        logger.info(f"Accepted file offer: {offer['filename']} from {offer['from']}")
        return True
    
    def reject_file_offer(self, file_id: str) -> bool:
        """Reject a file transfer offer"""
        if file_id in self.file_offers:
            offer = self.file_offers.pop(file_id)
            logger.info(f"Rejected file offer: {offer['filename']} from {offer['from']}")
            return True
        return False