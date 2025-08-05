#!/usr/bin/env python3
"""
Peer Integration Module
Connects the Textual UI with the existing P2P peer system
"""
import sys
import os
import threading
import time
from typing import Dict, Any, Optional, Callable

# Add parent directory to path for peer imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.core.message_handler import MessageHandler
from peer.config.settings import DEFAULT_VERBOSE_MODE


class TextualPeerInterface:
    """
    Interface between Textual UI and P2P peer system
    Manages the peer components and provides callbacks for UI updates
    """
    
    def __init__(self):
        # Initialize core peer components
        self.network_manager = NetworkManager()
        self.peer_manager = PeerManager()
        self.message_handler = MessageHandler(self.network_manager, self.peer_manager)
        
        # Connect peer manager with network manager
        self.peer_manager.set_network_manager(self.network_manager)
        
        # UI callback functions (set by the Textual app)
        self.on_message_received: Optional[Callable] = None
        self.on_peer_discovered: Optional[Callable] = None
        self.on_peer_lost: Optional[Callable] = None
        self.on_status_update: Optional[Callable] = None
        
        # Set up peer callbacks
        self.peer_manager.on_peer_discovered = self._handle_peer_discovered
        self.peer_manager.on_peer_lost = self._handle_peer_lost
        
        # Override message handlers to capture messages for UI
        self._setup_message_callbacks()
        
        # State tracking
        self.user_id = ""
        self.is_running = False
        self.verbose_mode = DEFAULT_VERBOSE_MODE
    
    def start_peer(self, username: str, verbose_mode: bool = DEFAULT_VERBOSE_MODE) -> bool:
        """
        Start the peer system with given username
        Returns True if successful, False otherwise
        """
        try:
            # Set up user ID
            network_info = self.network_manager.get_network_info()
            self.user_id = f"{username}@{network_info['local_ip']}"
            self.peer_manager.set_user_id(self.user_id)
            
            # Set verbose mode
            self.verbose_mode = verbose_mode
            self.message_handler.set_verbose_mode(verbose_mode)
            
            # Start network listening
            self.network_manager.start_listening()
            
            # Start peer discovery
            self.peer_manager.start_discovery()
            
            self.is_running = True
            
            # Notify UI of status update
            if self.on_status_update:
                self.on_status_update({
                    'user_id': self.user_id,
                    'local_address': f"{network_info['local_ip']}:{network_info['local_port']}",
                    'verbose_mode': verbose_mode,
                    'peer_count': 0
                })
            
            return True
            
        except Exception as e:
            if self.on_message_received:
                self.on_message_received("SYSTEM", "ERROR", f"Failed to start peer: {e}")
            return False
    
    def stop_peer(self):
        """Stop the peer system"""
        self.is_running = False
        
        # Stop discovery
        self.peer_manager.stop_discovery()
        
        # Stop network
        self.network_manager.stop_listening()
        
        if self.on_message_received:
            self.on_message_received("SYSTEM", "INFO", "Peer stopped")
    
    def send_post_message(self, content: str) -> int:
        """Send a broadcast POST message"""
        if not self.is_running:
            return 0
        
        sent_count = self.message_handler.send_post_message(content)
        
        # Show the message in our own UI
        if self.on_message_received:
            display_name = self.peer_manager.get_display_name(self.user_id)
            self.on_message_received("POST", display_name, content)
        
        return sent_count
    
    def send_dm_message(self, recipient: str, content: str) -> bool:
        """Send a direct message to a specific peer"""
        if not self.is_running:
            return False
        
        success = self.message_handler.send_dm_message(recipient, content)
        
        if success and self.on_message_received:
            self.on_message_received("SYSTEM", "INFO", f"DM sent to {recipient}")
        elif not success and self.on_message_received:
            self.on_message_received("SYSTEM", "ERROR", f"Failed to send DM to {recipient}")
        
        return success
    
    def send_profile_message(self, display_name: str, status: str, 
                           avatar_data: str = None, avatar_type: str = None) -> int:
        """Send a profile update message"""
        if not self.is_running:
            return 0
        
        sent_count = self.message_handler.send_profile_message(
            display_name, status, avatar_data, avatar_type
        )
        
        if self.on_message_received:
            self.on_message_received("SYSTEM", "INFO", 
                                   f"Profile updated and sent to {sent_count} peers")
        
        return sent_count
    
    def get_all_peers(self) -> Dict[str, Dict]:
        """Get all known peers"""
        if not self.is_running:
            return {}
        
        peers = self.peer_manager.get_all_peers()
        
        # Enhance peer data with display names and avatar info
        enhanced_peers = {}
        for user_id, peer_info in peers.items():
            enhanced_peers[user_id] = {
                **peer_info,
                'display_name': self.peer_manager.get_display_name(user_id),
                'avatar': user_id in self.peer_manager.user_profiles and 
                         self.peer_manager.user_profiles[user_id].get('avatar', False)
            }
        
        return enhanced_peers
    
    def toggle_verbose_mode(self) -> bool:
        """Toggle verbose mode and return new state"""
        self.verbose_mode = not self.verbose_mode
        self.message_handler.set_verbose_mode(self.verbose_mode)
        
        if self.on_message_received:
            mode_text = "ON" if self.verbose_mode else "OFF"
            self.on_message_received("SYSTEM", "INFO", f"Verbose mode: {mode_text}")
        
        return self.verbose_mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get current peer status"""
        if not self.is_running:
            return {
                'user_id': '',
                'local_address': '',
                'peer_count': 0,
                'verbose_mode': self.verbose_mode,
                'is_running': False
            }
        
        network_info = self.network_manager.get_network_info()
        peers = self.peer_manager.get_all_peers()
        
        return {
            'user_id': self.user_id,
            'local_address': f"{network_info['local_ip']}:{network_info['local_port']}",
            'peer_count': len(peers),
            'verbose_mode': self.verbose_mode,
            'is_running': True
        }
    
    def _setup_message_callbacks(self):
        """Set up callbacks to capture incoming messages for UI display"""
        # Store original handlers
        original_post_handler = self.message_handler.handle_post_message
        original_dm_handler = self.message_handler.handle_dm_message
        original_profile_handler = self.message_handler.handle_profile_message
        
        def enhanced_post_handler(msg_dict, addr):
            # Call original handler
            original_post_handler(msg_dict, addr)
            
            # Send to UI
            if self.on_message_received:
                user_id = msg_dict.get('USER_ID', 'Unknown')
                content = msg_dict.get('CONTENT', '')
                display_name = self.peer_manager.get_display_name(user_id)
                self.on_message_received("POST", display_name, content)
        
        def enhanced_dm_handler(msg_dict, addr):
            # Call original handler
            original_dm_handler(msg_dict, addr)
            
            # Send to UI
            if self.on_message_received:
                sender_id = msg_dict.get('FROM', 'Unknown')
                content = msg_dict.get('CONTENT', '')
                display_name = self.peer_manager.get_display_name(sender_id)
                self.on_message_received("DM", display_name, content)
        
        def enhanced_profile_handler(msg_dict, addr):
            # Call original handler
            original_profile_handler(msg_dict, addr)
            
            # Send to UI
            if self.on_message_received:
                user_id = msg_dict.get('USER_ID', 'Unknown')
                display_name = msg_dict.get('DISPLAY_NAME', user_id)
                status = msg_dict.get('STATUS', '')
                self.on_message_received("PROFILE", display_name, status)
        
        # Replace handlers
        self.message_handler.handle_post_message = enhanced_post_handler
        self.message_handler.handle_dm_message = enhanced_dm_handler
        self.message_handler.handle_profile_message = enhanced_profile_handler
    
    def _handle_peer_discovered(self, user_id: str):
        """Handle peer discovered event"""
        if self.on_peer_discovered:
            display_name = self.peer_manager.get_display_name(user_id)
            self.on_peer_discovered(user_id, display_name)
        
        if self.on_message_received:
            display_name = self.peer_manager.get_display_name(user_id)
            self.on_message_received("PEER_JOIN", display_name, "")
        
        # Update peer count in status
        if self.on_status_update:
            status = self.get_status()
            self.on_status_update(status)
    
    def _handle_peer_lost(self, user_id: str):
        """Handle peer lost event"""
        display_name = self.peer_manager.get_display_name(user_id)
        
        if self.on_peer_lost:
            self.on_peer_lost(user_id, display_name)
        
        if self.on_message_received:
            self.on_message_received("PEER_LEAVE", display_name, "")
        
        # Update peer count in status
        if self.on_status_update:
            status = self.get_status()
            self.on_status_update(status)
    
    def set_ui_callbacks(self, on_message_received: Callable = None,
                        on_peer_discovered: Callable = None,
                        on_peer_lost: Callable = None,
                        on_status_update: Callable = None):
        """Set callback functions for UI updates"""
        self.on_message_received = on_message_received
        self.on_peer_discovered = on_peer_discovered
        self.on_peer_lost = on_peer_lost
        self.on_status_update = on_status_update
