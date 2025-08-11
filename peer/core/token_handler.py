#!/usr/bin/env python3
"""
Token Handler Module
Handles token revocation and validation operations
"""
import time
import secrets

class TokenHandler:
    """Handles token-related operations"""
    
    def __init__(self, peer_manager, network_manager):
        self.peer_manager = peer_manager
        self.network_manager = network_manager
        self.verbose_mode = True
    
    def handle_token_revocation(self, msg_dict, addr):
        """
        Handle token revocation message
        
        Args:
            msg_dict (dict): The message dictionary
            addr (tuple): Sender address (ip, port)
            
        Returns:
            bool: True if token was successfully revoked
        """
        token = msg_dict.get('TOKEN')
        if not token:
            return False
            
        # Log the revocation if in verbose mode
        if self.verbose_mode:
            print(f"\nTYPE: REVOKE")
            print(f"TOKEN: {token}")
            
        # Revoke the token
        return self.peer_manager.revoke_token(token)
    
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
