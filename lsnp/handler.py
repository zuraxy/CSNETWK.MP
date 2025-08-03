import base64
import logging
import os
import time
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger('lsnp.handler')

class MessageHandler:
    """
    Handles incoming and outgoing messages for the LSNP protocol.
    Processes received messages and generates appropriate responses.
    """
    
    def __init__(self, transport, peer):
        """
        Initialize the message handler.
        
        Args:
            transport: The LSNPTransport instance for network communication
            peer: The local Peer instance
        """
        self.transport = transport
        self.peer = peer
        self.protocol = None  # Import later to avoid circular imports
        
        # Track processed message IDs to avoid duplicates
        self.processed_messages = set()
        
        # Maximum number of processed message IDs to keep
        self.max_processed_messages = 1000
        
        logger.info("Message handler initialized")
    
    def _get_protocol(self):
        """Lazy-load the protocol to avoid circular imports"""
        if self.protocol is None:
            from lsnp.protocol import Protocol
            self.protocol = Protocol
        return self.protocol
    
    def handle_message(self, data: bytes, sender_addr: Tuple[str, int]) -> None:
        """
        Process an incoming message.
        
        Args:
            data: The raw message bytes
            sender_addr: Tuple of (ip, port) the message came from
        """
        Protocol = self._get_protocol()
        
        try:
            # Decode the message
            message = Protocol.decode_message(data)
            
            # Extract message type
            if 'TYPE' not in message:
                logger.warning(f"Received message without TYPE from {sender_addr}")
                return
                
            message_type = message['TYPE']
            
            # Check for duplicate message (if it has an ID)
            message_id = message.get('MESSAGE_ID')
            if message_id and message_id in self.processed_messages:
                logger.debug(f"Ignoring duplicate message: {message_id}")
                return
                
            # Add to processed messages if it has an ID
            if message_id:
                self.processed_messages.add(message_id)
                # Trim set if it gets too large
                if len(self.processed_messages) > self.max_processed_messages:
                    self.processed_messages = set(list(self.processed_messages)[-self.max_processed_messages:])
            
            # Process based on message type
            if message_type == Protocol.TYPE_PING:
                self._handle_ping(message, sender_addr)
                
            elif message_type == Protocol.TYPE_PROFILE:
                self._handle_profile(message, sender_addr)
                
            elif message_type == Protocol.TYPE_POST:
                self._handle_post(message, sender_addr)
                
            elif message_type == Protocol.TYPE_DM:
                self._handle_dm(message, sender_addr)
                
            elif message_type == Protocol.TYPE_FOLLOW:
                self._handle_follow(message, sender_addr)
                
            elif message_type == Protocol.TYPE_UNFOLLOW:
                self._handle_unfollow(message, sender_addr)
                
            elif message_type == Protocol.TYPE_FILE_OFFER:
                self._handle_file_offer(message, sender_addr)
                
            elif message_type == Protocol.TYPE_FILE_CHUNK:
                self._handle_file_chunk(message, sender_addr)
                
            elif message_type == Protocol.TYPE_FILE_RECEIVED:
                self._handle_file_received(message, sender_addr)
                
            elif message_type == Protocol.TYPE_GROUP_CREATE:
                self._handle_group_create(message, sender_addr)
                
            elif message_type == Protocol.TYPE_GROUP_UPDATE:
                self._handle_group_update(message, sender_addr)
                
            elif message_type == Protocol.TYPE_GROUP_MESSAGE:
                self._handle_group_message(message, sender_addr)
                
            elif message_type == Protocol.TYPE_TICTACTOE_INVITE:
                self._handle_game_invite(message, sender_addr)
                
            elif message_type == Protocol.TYPE_TICTACTOE_MOVE:
                self._handle_game_move(message, sender_addr)
                
            elif message_type == Protocol.TYPE_ACK:
                self._handle_ack(message, sender_addr)
                
            elif message_type == Protocol.TYPE_REVOKE:
                self._handle_revoke(message, sender_addr)
                
            else:
                logger.warning(f"Unsupported message type: {message_type}")
            
        except Exception as e:
            logger.error(f"Error handling message from {sender_addr}: {e}")
    
    def _validate_token(self, message: Dict[str, Any], expected_scope: Optional[str] = None) -> bool:
        """
        Validate a token in a message.
        
        Args:
            message: The decoded message
            expected_scope: Expected token scope, if any
            
        Returns:
            True if token is valid, False otherwise
        """
        Protocol = self._get_protocol()
        
        if 'TOKEN' not in message:
            logger.warning("Message missing required TOKEN field")
            return False
            
        token = message['TOKEN']
        
        # Check if token is revoked
        if self.peer.is_token_revoked(token):
            logger.warning(f"Token is revoked: {token}")
            return False
        
        # Validate token
        is_valid, user_id, expiry, scope, error = Protocol.validate_token(token, expected_scope)
        
        if not is_valid:
            logger.warning(f"Invalid token: {error}")
            return False
            
        # Additional checks for user_id if present in message
        if 'USER_ID' in message and message['USER_ID'] != user_id:
            logger.warning(f"Token user_id mismatch: {message['USER_ID']} vs {user_id}")
            return False
            
        if 'FROM' in message and message['FROM'] != user_id:
            logger.warning(f"Token FROM mismatch: {message['FROM']} vs {user_id}")
            return False
        
        return True
    
    def _handle_ping(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle PING message"""
        if 'USER_ID' not in message:
            logger.warning("Received PING without USER_ID")
            return
            
        sender_ip, sender_port = sender_addr
        user_id = message['USER_ID']
        
        # Update peer information
        self.peer.add_or_update_from_ping(user_id, sender_ip, sender_port)
        logger.debug(f"Processed PING from {user_id}")
    
    def _handle_profile(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle PROFILE message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_BROADCAST):
            logger.warning(f"Invalid PROFILE token from {sender_addr}")
            return
            
        # Update peer information from profile
        self.peer.add_or_update_from_profile(message, sender_addr)
        logger.info(f"Processed PROFILE from {message.get('USER_ID')}")
    
    def _handle_post(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle POST message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_BROADCAST):
            logger.warning(f"Invalid POST token from {sender_addr}")
            return
            
        if 'USER_ID' not in message or 'CONTENT' not in message:
            logger.warning("Received POST without USER_ID or CONTENT")
            return
            
        user_id = message['USER_ID']
        content = message['CONTENT']
        message_id = message.get('MESSAGE_ID', 'unknown')
        timestamp = int(message.get('TIMESTAMP', time.time()))
        
        # Store the post if we follow this user or it's our own post
        if self.peer.is_following(user_id) or user_id == self.peer.user_id:
            self.peer.add_post(user_id, message_id, content, timestamp)
            
            # Display post
            display_name = self.peer.get_display_name(user_id)
            print(f"\n[POST from {display_name}]: {content}")
            
        # Send ACK
        if message_id != 'unknown':
            self._send_ack(message_id, sender_addr)
    
    def _handle_dm(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle DM message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_CHAT):
            logger.warning(f"Invalid DM token from {sender_addr}")
            return
            
        if 'FROM' not in message or 'TO' not in message or 'CONTENT' not in message:
            logger.warning("Received DM without FROM, TO, or CONTENT")
            return
            
        from_user = message['FROM']
        to_user = message['TO']
        content = message['CONTENT']
        message_id = message.get('MESSAGE_ID', 'unknown')
        timestamp = int(message.get('TIMESTAMP', time.time()))
        
        # Check if this DM is for us
        if to_user == self.peer.user_id:
            # Store the DM
            self.peer.add_received_dm(message_id, from_user, content, timestamp)
            
            # Display DM
            display_name = self.peer.get_display_name(from_user)
            print(f"\n[DM from {display_name}]: {content}")
            
            # Send ACK
            if message_id != 'unknown':
                self._send_ack(message_id, sender_addr)
        else:
            logger.warning(f"Received DM not addressed to us: {to_user}")
    
    def _handle_follow(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle FOLLOW message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_FOLLOW):
            logger.warning(f"Invalid FOLLOW token from {sender_addr}")
            return
            
        if 'FROM' not in message or 'TO' not in message:
            logger.warning("Received FOLLOW without FROM or TO")
            return
            
        from_user = message['FROM']
        to_user = message['TO']
        
        # If someone is following us
        if to_user == self.peer.user_id:
            # Update our follower list
            self.peer.add_follower(from_user)
            
            # Update peer info if not already known
            if from_user not in self.peer.known_peers:
                sender_ip, sender_port = sender_addr
                username = from_user.split('@')[0] if '@' in from_user else from_user
                self.peer.update_peer(from_user, ip=sender_ip, port=sender_port)
            
            # Display notification
            display_name = self.peer.get_display_name(from_user)
            print(f"\n{display_name} is now following you")
    
    def _handle_unfollow(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle UNFOLLOW message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_FOLLOW):
            logger.warning(f"Invalid UNFOLLOW token from {sender_addr}")
            return
            
        if 'FROM' not in message or 'TO' not in message:
            logger.warning("Received UNFOLLOW without FROM or TO")
            return
            
        from_user = message['FROM']
        to_user = message['TO']
        
        # If someone is unfollowing us
        if to_user == self.peer.user_id:
            # Update our follower list
            self.peer.remove_follower(from_user)
            
            # Display notification
            display_name = self.peer.get_display_name(from_user)
            print(f"\n{display_name} is no longer following you")
    
    def _handle_file_offer(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle FILE_OFFER message"""
        if not self._validate_token(message, self._get_protocol().SCOPE_FILE):
            logger.warning(f"Invalid FILE_OFFER token from {sender_addr}")
            return
            
        if 'FROM' not in message or 'TO' not in message or 'FILE_ID' not in message:
            logger.warning("Received FILE_OFFER without FROM, TO, or FILE_ID")
            return
            
        from_user = message['FROM']
        to_user = message['TO']
        file_id = message['FILE_ID']
        filename = message.get('FILENAME', 'unnamed-file')
        filesize = int(message.get('SIZE', 0))
        filetype = message.get('TYPE', 'application/octet-stream')
        description = message.get('DESCRIPTION', '')
        
        # If this file offer is for us
        if to_user == self.peer.user_id:
            # Store the file offer
            self.peer.process_file_offer(file_id, from_user, filename, filesize, filetype, description)
            
            # Display notification
            display_name = self.peer.get_display_name(from_user)
            print(f"\n[FILE OFFER from {display_name}]: {filename} ({filesize} bytes)")
            print(f"Description: {description}")
            print(f"Type 'FILE ACCEPT {file_id}' to accept or 'FILE REJECT {file_id}' to reject")
    
    def _handle_file_chunk(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle FILE_CHUNK message"""
        # Basic implementation - would need to be expanded for real file transfer
        pass
    
    def _handle_file_received(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle FILE_RECEIVED message"""
        # Basic implementation - would need to be expanded for real file transfer
        pass
    
    def _handle_group_create(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle GROUP_CREATE message"""
        # Basic implementation - would need to be expanded for group functionality
        pass
    
    def _handle_group_update(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle GROUP_UPDATE message"""
        # Basic implementation - would need to be expanded for group functionality
        pass
    
    def _handle_group_message(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle GROUP_MESSAGE message"""
        # Basic implementation - would need to be expanded for group functionality
        pass
    
    def _handle_game_invite(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle TICTACTOE_INVITE message"""
        # Basic implementation - would need to be expanded for game functionality
        pass
    
    def _handle_game_move(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle TICTACTOE_MOVE message"""
        # Basic implementation - would need to be expanded for game functionality
        pass
    
    def _handle_ack(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle ACK message"""
        if 'MESSAGE_ID' not in message:
            logger.warning("Received ACK without MESSAGE_ID")
            return
            
        message_id = message['MESSAGE_ID']
        status = message.get('STATUS', 'RECEIVED')
        
        logger.debug(f"Received ACK for message {message_id}: {status}")
        # Additional ACK handling could be implemented here
    
    def _handle_revoke(self, message: Dict[str, Any], sender_addr: Tuple[str, int]) -> None:
        """Handle REVOKE message"""
        if 'TOKEN' not in message:
            logger.warning("Received REVOKE without TOKEN")
            return
            
        token = message['TOKEN']
        
        # Add token to revocation list
        self.peer.revoke_token(token)
        logger.info(f"Added token to revocation list: {token}")
    
    def _send_ack(self, message_id: str, recipient_addr: Tuple[str, int]) -> None:
        """Send ACK for a received message"""
        Protocol = self._get_protocol()
        
        # Create ACK message
        ack_data = Protocol.create_ack_message(message_id)
        
        # Encode and send
        encoded_ack = Protocol.encode_message(ack_data)
        self.transport.send(encoded_ack, recipient_addr)
        
        logger.debug(f"Sent ACK for {message_id} to {recipient_addr}")
    
    # Outgoing message methods
    
    def send_ping(self) -> None:
        """Send a PING message to announce presence"""
        Protocol = self._get_protocol()
        
        # Create PING message
        ping_data = Protocol.create_ping_message(self.peer.user_id)
        
        # Encode and broadcast
        encoded_ping = Protocol.encode_message(ping_data)
        self.transport.broadcast(encoded_ping)
        
        # Update last ping time
        self.peer.record_broadcast_time('PING')
        logger.debug("Broadcast PING message")
    
    def send_profile(self) -> None:
        """Send a PROFILE message with user information"""
        Protocol = self._get_protocol()
        
        # Create PROFILE message
        profile_data = Protocol.create_profile_message(
            user_id=self.peer.user_id,
            display_name=self.peer.display_name,
            status=self.peer.status,
            avatar_path=self.peer.avatar_path
        )
        
        # Encode and broadcast
        encoded_profile = Protocol.encode_message(profile_data)
        self.transport.broadcast(encoded_profile)
        
        # Update last profile time
        self.peer.record_broadcast_time('PROFILE')
        logger.info("Broadcast PROFILE message")
    
    def update_profile_with_avatar(self, avatar_path: str) -> bool:
        """Update profile with a new avatar and broadcast it"""
        if not os.path.exists(avatar_path):
            logger.error(f"Avatar file not found: {avatar_path}")
            return False
            
        # Update peer state
        self.peer.update_profile(avatar_path=avatar_path)
        
        # Send profile broadcast
        self.send_profile()
        return True
    
    def send_post(self, content: str) -> bool:
        """Send a POST message to the network"""
        Protocol = self._get_protocol()
        
        # Create POST message
        post_data = Protocol.create_post_message(
            user_id=self.peer.user_id,
            content=content
        )
        
        # Encode and broadcast
        encoded_post = Protocol.encode_message(post_data)
        success = self.transport.broadcast(encoded_post)
        
        if success:
            # Store in local posts
            message_id = post_data['MESSAGE_ID']
            timestamp = int(post_data.get('TIMESTAMP', time.time()))
            self.peer.add_post(self.peer.user_id, message_id, content, timestamp)
            logger.info(f"Broadcast POST: {content[:20]}...")
        
        return success
    
    def send_dm(self, recipient: str, content: str) -> bool:
        """Send a direct message to a specific user"""
        Protocol = self._get_protocol()
        
        # Get recipient address
        ip, port = self.peer.get_peer_address(recipient)
        if not ip or not port:
            logger.error(f"Cannot send DM: Unknown recipient {recipient}")
            return False
        
        # Create DM message
        dm_data = Protocol.create_dm_message(
            from_user=self.peer.user_id,
            to_user=recipient,
            content=content
        )
        
        # Encode and send
        encoded_dm = Protocol.encode_message(dm_data)
        success = self.transport.send(encoded_dm, (ip, port))
        
        if success:
            # Store in sent DMs
            message_id = dm_data['MESSAGE_ID']
            timestamp = int(dm_data.get('TIMESTAMP', time.time()))
            self.peer.add_sent_dm(message_id, recipient, content, timestamp)
            logger.info(f"Sent DM to {recipient}: {content[:20]}...")
        
        return success
    
    def follow_user(self, user_id: str) -> bool:
        """Send a FOLLOW message to a user"""
        Protocol = self._get_protocol()
        
        # Check if user exists
        ip, port = self.peer.get_peer_address(user_id)
        if not ip or not port:
            logger.error(f"Cannot follow: Unknown user {user_id}")
            return False
        
        # Create FOLLOW message
        follow_data = Protocol.create_follow_message(
            from_user=self.peer.user_id,
            to_user=user_id
        )
        
        # Encode and send
        encoded_follow = Protocol.encode_message(follow_data)
        success = self.transport.send(encoded_follow, (ip, port))
        
        if success:
            # Update local following list
            self.peer.follow_user(user_id)
            logger.info(f"Sent FOLLOW to {user_id}")
        
        return success
    
    def unfollow_user(self, user_id: str) -> bool:
        """Send an UNFOLLOW message to a user"""
        Protocol = self._get_protocol()
        
        # Check if user exists
        ip, port = self.peer.get_peer_address(user_id)
        if not ip or not port:
            logger.error(f"Cannot unfollow: Unknown user {user_id}")
            return False
        
        # Create UNFOLLOW message
        unfollow_data = Protocol.create_unfollow_message(
            from_user=self.peer.user_id,
            to_user=user_id
        )
        
        # Encode and send
        encoded_unfollow = Protocol.encode_message(unfollow_data)
        success = self.transport.send(encoded_unfollow, (ip, port))
        
        if success:
            # Update local following list
            self.peer.unfollow_user(user_id)
            logger.info(f"Sent UNFOLLOW to {user_id}")
        
        return success
    
    def send_file(self, recipient: str, file_path: str) -> bool:
        """Initiate file transfer by sending FILE_OFFER"""
        # This is a simplified implementation - real file transfer
        # would require chunking, checksums, etc.
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Implementation would be expanded for real file transfer
        logger.info(f"File transfer not fully implemented")
        return False
    
    def create_group(self, group_name: str) -> bool:
        """Create a new group"""
        # Implementation would be expanded for group functionality
        logger.info(f"Group creation not fully implemented")
        return False
    
    def join_group(self, group_id: str) -> bool:
        """Join an existing group"""
        # Implementation would be expanded for group functionality
        logger.info(f"Group joining not fully implemented")
        return False
    
    def send_group_message(self, group_id: str, content: str) -> bool:
        """Send a message to a group"""
        # Implementation would be expanded for group functionality
        logger.info(f"Group messaging not fully implemented")
        return False
    
    def invite_to_game(self, opponent: str) -> bool:
        """Invite another user to play Tic Tac Toe"""
        # Implementation would be expanded for game functionality
        logger.info(f"Game functionality not fully implemented")
        return False