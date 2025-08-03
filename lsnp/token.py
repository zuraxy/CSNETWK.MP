import time
import secrets
import hashlib
import logging
from typing import Tuple, Optional, Dict, Set

logger = logging.getLogger('lsnp.token')

class TokenManager:
    """
    Advanced token management for the LSNP protocol.
    Handles token creation, validation, revocation and security.
    """
    
    # Token scopes - duplicated from Protocol for convenience
    SCOPE_CHAT = 'chat'
    SCOPE_BROADCAST = 'broadcast'
    SCOPE_FOLLOW = 'follow'
    SCOPE_FILE = 'file'
    SCOPE_GROUP = 'group'
    SCOPE_GAME = 'game'
    
    # Default TTL values for different token types
    DEFAULT_TTL = {
        SCOPE_CHAT: 3600,      # 1 hour
        SCOPE_BROADCAST: 3600,  # 1 hour
        SCOPE_FOLLOW: 86400,    # 24 hours
        SCOPE_FILE: 7200,       # 2 hours
        SCOPE_GROUP: 86400,     # 24 hours
        SCOPE_GAME: 7200        # 2 hours
    }
    
    def __init__(self):
        """Initialize the token manager"""
        # Token revocation storage
        self.revoked_tokens: Set[str] = set()
        self.revoked_hashes: Set[str] = set()
        
        # Max size of revocation lists
        self.max_revocations = 1000
        
        logger.debug("Token manager initialized")
    
    def create_token(self, user_id: str, scope: str, ttl: Optional[int] = None) -> str:
        """
        Create a new token for a specific user and scope.
        
        Args:
            user_id: User ID in the format username@ipaddress
            scope: Token scope (chat, broadcast, etc.)
            ttl: Time-to-live in seconds (defaults to scope-specific value)
            
        Returns:
            Formatted token string
        """
        if ttl is None:
            ttl = self.DEFAULT_TTL.get(scope, 3600)
            
        expiry = int(time.time()) + ttl
        token = f"{user_id}|{expiry}|{scope}"
        
        logger.debug(f"Created {scope} token for {user_id}, expires in {ttl}s")
        return token
    
    def validate_token(self, token: str, expected_scope: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[int], Optional[str], str]:
        """
        Validate a token's format, expiration and scope.
        
        Args:
            token: Token string to validate
            expected_scope: Optional scope to check against
            
        Returns:
            Tuple of (is_valid, user_id, expiry, scope, error_message)
        """
        try:
            # Check if token is revoked
            if self.is_token_revoked(token):
                return (False, None, None, None, "Token has been revoked")
                
            parts = token.split('|')
            if len(parts) != 3:
                return (False, None, None, None, "Invalid token format")
                
            user_id, expiry_str, scope = parts
            
            try:
                expiry = int(expiry_str)
            except ValueError:
                return (False, None, None, None, "Invalid expiry timestamp")
                
            # Check expiration
            if expiry < int(time.time()):
                return (False, user_id, expiry, scope, "Token expired")
                
            # Check scope if provided
            if expected_scope and scope != expected_scope:
                return (False, user_id, expiry, scope, f"Invalid scope (expected {expected_scope}, got {scope})")
                
            return (True, user_id, expiry, scope, "Valid token")
            
        except Exception as e:
            return (False, None, None, None, f"Token validation error: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token so it can no longer be used.
        
        Args:
            token: Token to revoke
            
        Returns:
            Success status
        """
        # Store both the full token and its hash for efficient lookups
        self.revoked_tokens.add(token)
        token_hash = self._hash_token(token)
        self.revoked_hashes.add(token_hash)
        
        # Cleanup if lists get too large
        if len(self.revoked_tokens) > self.max_revocations:
            # In a real implementation, we would want to expire old tokens
            # based on their expiry time. For simplicity, we just trim the sets.
            self.revoked_tokens = set(list(self.revoked_tokens)[-self.max_revocations:])
            self.revoked_hashes = set(list(self.revoked_hashes)[-self.max_revocations:])
            
        logger.info(f"Token revoked: {token[:10]}...")
        return True
    
    def is_token_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: Token to check
            
        Returns:
            True if token is revoked, False otherwise
        """
        # Check both the full token and its hash
        if token in self.revoked_tokens:
            return True
            
        token_hash = self._hash_token(token)
        return token_hash in self.revoked_hashes
    
    def _hash_token(self, token: str) -> str:
        """
        Create a hash of a token for efficient storage and lookup.
        
        Args:
            token: Token string
            
        Returns:
            SHA-256 hash of the token as a hex string
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def cleanup_expired_revocations(self) -> int:
        """
        Remove expired tokens from the revocation list.
        
        Returns:
            Number of tokens removed
        """
        current_time = int(time.time())
        tokens_to_remove = []
        
        # Find expired tokens
        for token in self.revoked_tokens:
            try:
                parts = token.split('|')
                if len(parts) == 3:
                    _, expiry_str, _ = parts
                    expiry = int(expiry_str)
                    
                    # If token has expired, no need to keep it in revocation list
                    if expiry < current_time:
                        tokens_to_remove.append(token)
            except:
                # If token format is invalid, keep it in revocation list
                pass
        
        # Remove expired tokens
        for token in tokens_to_remove:
            self.revoked_tokens.remove(token)
            token_hash = self._hash_token(token)
            if token_hash in self.revoked_hashes:
                self.revoked_hashes.remove(token_hash)
        
        if tokens_to_remove:
            logger.info(f"Cleaned up {len(tokens_to_remove)} expired token revocations")
            
        return len(tokens_to_remove)
    
    def generate_secure_id(self, prefix: str = "") -> str:
        """
        Generate a secure random identifier (for message IDs, file IDs, etc.)
        
        Args:
            prefix: Optional prefix for the ID
            
        Returns:
            Secure random identifier string
        """
        random_hex = secrets.token_hex(8)  # 64 bits of randomness
        if prefix:
            return f"{prefix}-{random_hex}"
        return random_hex


# Create a global instance for easy importing
token_manager = TokenManager()


def create_token(user_id: str, scope: str, ttl: Optional[int] = None) -> str:
    """
    Convenience function to create a token.
    
    Args:
        user_id: User ID in the format username@ipaddress
        scope: Token scope (chat, broadcast, etc.)
        ttl: Time-to-live in seconds (defaults to scope-specific value)
        
    Returns:
        Formatted token string
    """
    return token_manager.create_token(user_id, scope, ttl)


def validate_token(token: str, expected_scope: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[int], Optional[str], str]:
    """
    Convenience function to validate a token.
    
    Args:
        token: Token string to validate
        expected_scope: Optional scope to check against
        
    Returns:
        Tuple of (is_valid, user_id, expiry, scope, error_message)
    """
    return token_manager.validate_token(token, expected_scope)


def revoke_token(token: str) -> bool:
    """
    Convenience function to revoke a token.
    
    Args:
        token: Token to revoke
        
    Returns:
        Success status
    """
    return token_manager.revoke_token(token)


def is_token_revoked(token: str) -> bool:
    """
    Convenience function to check if a token is revoked.
    
    Args:
        token: Token to check
        
    Returns:
        True if token is revoked, False otherwise
    """
    return token_manager.is_token_revoked(token)