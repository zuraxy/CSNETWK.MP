#!/usr/bin/env python3
"""
Token Management Module
Handles creation, validation, and revocation of security tokens
"""
import time
import hashlib
import os
import base64

class TokenManager:
    """
    Manages security tokens for peer-to-peer communication
    Handles token creation, validation, revocation, and scope enforcement
    """
    
    # Token scopes
    SCOPE_CHAT = "chat"           # For direct messages
    SCOPE_FILE = "file"           # For file transfers
    SCOPE_BROADCAST = "broadcast" # For public posts and interactions
    SCOPE_FOLLOW = "follow"       # For follow/unfollow operations
    SCOPE_GAME = "game"           # For game interactions
    SCOPE_GROUP = "group"         # For group operations
    
    # Default token TTL (Time To Live) in seconds
    DEFAULT_TOKEN_TTL = 3600  # 1 hour
    
    def __init__(self):
        # Dictionary to store revoked tokens: {token_hash: revocation_time}
        self.revoked_tokens = {}
        
        # Map message types to required scopes
        self.message_type_scopes = {
            'POST': self.SCOPE_BROADCAST,
            'LIKE': self.SCOPE_BROADCAST,
            'DM': self.SCOPE_CHAT,
            'FOLLOW': self.SCOPE_FOLLOW,
            'UNFOLLOW': self.SCOPE_FOLLOW,
            'FILE_OFFER': self.SCOPE_FILE,
            'FILE_CHUNK': self.SCOPE_FILE,
            'GROUP_CREATE': self.SCOPE_GROUP,
            'GROUP_UPDATE': self.SCOPE_GROUP,
            'GROUP_MESSAGE': self.SCOPE_GROUP,
            'TICTACTOE_MOVE': self.SCOPE_GAME,
            'TICTACTOE_RESULT': self.SCOPE_GAME
        }
    
    def create_token(self, user_id, scope, ttl=None):
        """
        Create a new token with specified scope and time-to-live
        
        Args:
            user_id (str): User identifier (e.g. 'alice@192.168.1.11')
            scope (str): Token scope (chat, file, broadcast, etc.)
            ttl (int, optional): Time-to-live in seconds. Defaults to DEFAULT_TOKEN_TTL.
            
        Returns:
            str: Formatted token string
        """
        if ttl is None:
            ttl = self.DEFAULT_TOKEN_TTL
            
        # Calculate expiration timestamp
        expiration = int(time.time()) + ttl
        
        # Format: user_id|expiration_timestamp|scope
        token = f"{user_id}|{expiration}|{scope}"
        return token
    
    def validate_token(self, token, required_scope=None, peer_ip=None):
        """
        Validate a token based on expiration, scope, and revocation status
        
        Args:
            token (str): Token to validate
            required_scope (str, optional): Required scope for operation
            peer_ip (str, optional): IP address for additional validation
            
        Returns:
            tuple: (is_valid, reason) - Validation result and reason if invalid
        """
        if not token:
            return False, "Token missing"
            
        try:
            # Parse token parts
            parts = token.split('|')
            if len(parts) != 3:
                return False, "Invalid token format"
                
            user_id, expiration_str, token_scope = parts
            expiration = int(expiration_str)
            
            # Check if token is expired
            current_time = int(time.time())
            if current_time > expiration:
                return False, "Token expired"
            
            # Check if token is revoked
            token_hash = self._hash_token(token)
            if token_hash in self.revoked_tokens:
                return False, "Token revoked"
            
            # Verify IP match if needed
            #if peer_ip and '@' in user_id:
            #    token_ip = user_id.split('@')[1]
            #    if token_ip != peer_ip:
            #        return False, "IP mismatch"
            
            # Check scope if required
            if required_scope and token_scope != required_scope:
                return False, f"Invalid scope (required: {required_scope}, got: {token_scope})"
                
            return True, None
            
        except Exception as e:
            return False, f"Token validation error: {str(e)}"
    
    def revoke_token(self, token):
        """
        Revoke a token before its natural expiration
        
        Args:
            token (str): Token to revoke
            
        Returns:
            bool: True if token was successfully revoked
        """
        token_hash = self._hash_token(token)
        self.revoked_tokens[token_hash] = int(time.time())
        return True
    
    def revoke_all_user_tokens(self, user_id):
        """
        Placeholder for revoking all tokens for a specific user
        In a real implementation, this would require tracking tokens by user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            bool: True if operation was successful
        """
        # This is a simplified implementation
        # In reality, we would need to track tokens by user
        # For now, we'll just add a special revocation entry
        revocation_marker = f"ALL_TOKENS:{user_id}:{int(time.time())}"
        self.revoked_tokens[revocation_marker] = int(time.time())
        return True
    
    def get_required_scope_for_message_type(self, message_type):
        """
        Get the required scope for a specific message type
        
        Args:
            message_type (str): The type of message
            
        Returns:
            str: Required scope or None if no specific scope is required
        """
        return self.message_type_scopes.get(message_type)
    
    def cleanup_revoked_tokens(self, max_age=86400):
        """
        Remove old revoked tokens to prevent memory leaks
        
        Args:
            max_age (int): Maximum age of revoked tokens in seconds
            
        Returns:
            int: Number of tokens removed
        """
        current_time = int(time.time())
        tokens_to_remove = []
        
        for token_hash, revocation_time in self.revoked_tokens.items():
            if current_time - revocation_time > max_age:
                tokens_to_remove.append(token_hash)
        
        for token_hash in tokens_to_remove:
            del self.revoked_tokens[token_hash]
            
        return len(tokens_to_remove)
    
    def _hash_token(self, token):
        """
        Create a hash of a token for efficient storage in revocation list
        
        Args:
            token (str): Token to hash
            
        Returns:
            str: Hash of the token
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
