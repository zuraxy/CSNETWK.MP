import time
import secrets
import base64
import mimetypes
import os

class Protocol:
    """
    LSNP Protocol implementation handling message encoding, decoding and formatting
    according to RFC specifications.
    """
    
    # Message types
    TYPE_PING = 'PING'
    TYPE_PROFILE = 'PROFILE'
    TYPE_POST = 'POST'
    TYPE_DM = 'DM'
    TYPE_ACK = 'ACK'
    TYPE_FOLLOW = 'FOLLOW'
    TYPE_UNFOLLOW = 'UNFOLLOW'
    TYPE_FILE_OFFER = 'FILE_OFFER'
    TYPE_FILE_CHUNK = 'FILE_CHUNK'
    TYPE_FILE_RECEIVED = 'FILE_RECEIVED'
    TYPE_REVOKE = 'REVOKE'
    TYPE_LIKE = 'LIKE'
    TYPE_GROUP_CREATE = 'GROUP_CREATE'
    TYPE_GROUP_UPDATE = 'GROUP_UPDATE'
    TYPE_GROUP_MESSAGE = 'GROUP_MESSAGE'
    TYPE_TICTACTOE_INVITE = 'TICTACTOE_INVITE'
    TYPE_TICTACTOE_MOVE = 'TICTACTOE_MOVE'
    TYPE_TICTACTOE_RESULT = 'TICTACTOE_RESULT'
    
    # Token scopes
    SCOPE_CHAT = 'chat'
    SCOPE_BROADCAST = 'broadcast'
    SCOPE_FOLLOW = 'follow'
    SCOPE_FILE = 'file'
    SCOPE_GROUP = 'group'
    SCOPE_GAME = 'game'
    
    @staticmethod
    def encode_message(data: dict) -> bytes:
        """
        Encode a dictionary into an LSNP message.
        
        Args:
            data: Dictionary containing key-value pairs
            
        Returns:
            Encoded message as bytes
        """
        return ('\n'.join(f"{k}:{v}" for k, v in data.items()) + '\n\n').encode('utf-8')
    
    @staticmethod
    def decode_message(message: bytes) -> dict:
        """
        Decode an LSNP message into a dictionary.
        
        Args:
            message: LSNP message as bytes
            
        Returns:
            Dictionary with parsed key-value pairs
        """
        text = message.decode('utf-8')
        pairs = (item.split(':', 1) for item in text.split('\n') if ':' in item)
        return {k: v for k, v in pairs}
    
    @staticmethod
    def generate_message_id() -> str:
        """Generate a random message ID (64-bit hex)"""
        return secrets.token_hex(8)
    
    @staticmethod
    def create_token(user_id: str, ttl: int, scope: str) -> str:
        """
        Create an LSNP authentication token.
        
        Args:
            user_id: User ID (username@ip)
            ttl: Time-to-live in seconds
            scope: Token scope (chat, broadcast, etc.)
            
        Returns:
            Formatted token string
        """
        expiry = int(time.time()) + ttl
        return f"{user_id}|{expiry}|{scope}"
    
    @staticmethod
    def validate_token(token: str, expected_scope: str = None) -> tuple:
        """
        Validate a token's format, expiration and scope.
        
        Args:
            token: Token string to validate
            expected_scope: Optional scope to check against
            
        Returns:
            Tuple of (is_valid, user_id, expiry, scope, error_message)
        """
        try:
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
    
    @staticmethod
    def create_ping_message(user_id: str) -> dict:
        """Create a PING message"""
        return {
            'TYPE': Protocol.TYPE_PING,
            'USER_ID': user_id
        }
    
    @staticmethod
    def create_profile_message(user_id: str, display_name: str, status: str, 
                             avatar_path: str = None, ttl: int = 3600) -> dict:
        """Create a PROFILE message, optionally with avatar"""
        timestamp = int(time.time())
        message = {
            'TYPE': Protocol.TYPE_PROFILE,
            'USER_ID': user_id,
            'DISPLAY_NAME': display_name,
            'STATUS': status,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': Protocol.generate_message_id(),
            'TOKEN': Protocol.create_token(user_id, ttl, Protocol.SCOPE_BROADCAST)
        }
        
        # Add avatar if provided and file exists
        if avatar_path and os.path.exists(avatar_path):
            try:
                # Read and encode image
                with open(avatar_path, 'rb') as f:
                    avatar_bytes = f.read()
                    avatar_b64 = base64.b64encode(avatar_bytes).decode('utf-8')
                
                # Get MIME type
                mime_type, _ = mimetypes.guess_type(avatar_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/png'  # Default to PNG
                
                # Add avatar fields
                message['AVATAR_TYPE'] = mime_type
                message['AVATAR_ENCODING'] = 'base64'
                message['AVATAR_DATA'] = avatar_b64
            except Exception as e:
                print(f"Error processing avatar: {e}")
        
        return message
    
    @staticmethod
    def create_post_message(user_id: str, content: str, ttl: int = 3600) -> dict:
        """Create a POST message"""
        timestamp = int(time.time())
        return {
            'TYPE': Protocol.TYPE_POST,
            'USER_ID': user_id,
            'CONTENT': content,
            'TTL': str(ttl),
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': Protocol.generate_message_id(),
            'TOKEN': Protocol.create_token(user_id, ttl, Protocol.SCOPE_BROADCAST)
        }
    
    @staticmethod
    def create_dm_message(from_user: str, to_user: str, content: str, ttl: int = 3600) -> dict:
        """Create a DM message"""
        timestamp = int(time.time())
        return {
            'TYPE': Protocol.TYPE_DM,
            'FROM': from_user,
            'TO': to_user,
            'CONTENT': content,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': Protocol.generate_message_id(),
            'TOKEN': Protocol.create_token(from_user, ttl, Protocol.SCOPE_CHAT)
        }
    
    @staticmethod
    def create_follow_message(from_user: str, to_user: str, ttl: int = 3600) -> dict:
        """Create a FOLLOW message"""
        timestamp = int(time.time())
        return {
            'TYPE': Protocol.TYPE_FOLLOW,
            'FROM': from_user,
            'TO': to_user,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': Protocol.generate_message_id(),
            'TOKEN': Protocol.create_token(from_user, ttl, Protocol.SCOPE_FOLLOW)
        }
    
    @staticmethod
    def create_unfollow_message(from_user: str, to_user: str, ttl: int = 3600) -> dict:
        """Create an UNFOLLOW message"""
        timestamp = int(time.time())
        return {
            'TYPE': Protocol.TYPE_UNFOLLOW,
            'FROM': from_user,
            'TO': to_user,
            'TIMESTAMP': str(timestamp),
            'MESSAGE_ID': Protocol.generate_message_id(),
            'TOKEN': Protocol.create_token(from_user, ttl, Protocol.SCOPE_FOLLOW)
        }
    
    @staticmethod
    def create_ack_message(message_id: str, status: str = 'RECEIVED') -> dict:
        """Create an ACK message"""
        return {
            'TYPE': Protocol.TYPE_ACK,
            'MESSAGE_ID': message_id,
            'STATUS': status
        }