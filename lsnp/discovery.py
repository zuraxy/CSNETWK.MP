import threading
import time
import logging
from typing import Optional

logger = logging.getLogger('lsnp.discovery')

def start_discovery(transport, peer, interval: int = 300) -> threading.Thread:
    """
    Start a background thread that periodically announces this peer's presence
    by broadcasting PING or PROFILE messages to the network.
    
    According to the RFC, peers should broadcast either PING or PROFILE every 
    300 seconds, with PROFILE being sent at least once every 300 seconds.
    
    Args:
        transport: The LSNPTransport instance for network communication
        peer: The local Peer instance
        interval: Broadcast interval in seconds (default: 300 per RFC)
        
    Returns:
        The discovery thread instance
    """
    def discovery_loop():
        logger.info("Starting discovery broadcast loop")
        
        while True:
            try:
                current_time = time.time()
                
                # Decide whether to send PING or PROFILE
                # PROFILE should be sent if it hasn't been sent in the last interval
                if peer.should_send_profile(interval):
                    logger.debug("Sending PROFILE broadcast")
                    send_profile_broadcast(transport, peer)
                    peer.record_broadcast_time('PROFILE')
                else:
                    logger.debug("Sending PING broadcast")
                    send_ping_broadcast(transport, peer)
                    peer.record_broadcast_time('PING')
                    
                # Sleep until next broadcast interval
                # We calculate how long to sleep based on the elapsed time
                elapsed = time.time() - current_time
                sleep_time = max(interval - elapsed, 1)  # At least 1 second
                
                logger.debug(f"Next discovery broadcast in {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                # Short sleep to avoid tight loop if there's an error
                time.sleep(5)
    
    # Start the discovery thread
    thread = threading.Thread(target=discovery_loop, daemon=True)
    thread.start()
    logger.info("Discovery thread started")
    return thread

def send_ping_broadcast(transport, peer) -> bool:
    """
    Send a PING broadcast to the network.
    
    Args:
        transport: The LSNPTransport instance
        peer: The local Peer instance
        
    Returns:
        Success status
    """
    from lsnp.protocol import Protocol
    
    # Create PING message
    ping_data = Protocol.create_ping_message(peer.user_id)
    
    # Encode and broadcast
    encoded_ping = Protocol.encode_message(ping_data)
    return transport.broadcast(encoded_ping)

def send_profile_broadcast(transport, peer) -> bool:
    """
    Send a PROFILE broadcast to the network.
    
    Args:
        transport: The LSNPTransport instance
        peer: The local Peer instance
        
    Returns:
        Success status
    """
    from lsnp.protocol import Protocol
    
    # Create PROFILE message
    profile_data = Protocol.create_profile_message(
        user_id=peer.user_id,
        display_name=peer.display_name,
        status=peer.status,
        avatar_path=peer.avatar_path
    )
    
    # Encode and broadcast
    encoded_profile = Protocol.encode_message(profile_data)
    return transport.broadcast(encoded_profile)

def schedule_cleanup(peer, interval: int = 1800) -> threading.Thread:
    """
    Start a background thread to periodically clean up inactive peers.
    
    Args:
        peer: The local Peer instance
        interval: Cleanup interval in seconds (default: 1800 - 30 minutes)
        
    Returns:
        The cleanup thread instance
    """
    def cleanup_loop():
        logger.info("Starting inactive peer cleanup loop")
        
        while True:
            try:
                # Sleep first to allow initial discovery
                time.sleep(interval)
                
                # Perform cleanup
                removed = peer.cleanup_inactive_peers(interval)
                if removed > 0:
                    logger.info(f"Cleaned up {removed} inactive peers")
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Short sleep to avoid tight loop if there's an error
                time.sleep(5)
    
    # Start the cleanup thread
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info("Cleanup thread started")
    return thread