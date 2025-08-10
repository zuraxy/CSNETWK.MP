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
            try:
                if self.running:
                    self.announce_presence()
                    self.cleanup_old_peers()
                    
                # Check if we should continue running before sleeping
                if self.running:
                    time.sleep(self.discovery_interval)
            except Exception:
                if self.running:
                    time.sleep(1)  # Short sleep before retry
    
    def announce_presence(self):
        """Broadcast presence announcement"""
        if not self.network_manager or not self.user_id:
            return False
        
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
            
            # Update peer info
            port = msg_dict.get('PORT', addr[1])
            self.update_peer_info(sender_id, addr[0], port)
            
            # Send discovery response
            self.send_discovery_response(addr[0], int(port))
            
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
    
    def _generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)