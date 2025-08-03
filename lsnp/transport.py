import socket
import threading
import logging
import time
from typing import Callable, Tuple, Optional

logger = logging.getLogger('lsnp.transport')

class LSNPTransport:
    """
    Handles UDP socket communication for the LSNP protocol.
    Manages both broadcast and unicast messaging.
    """
    
    def __init__(self, port: int = 50999, broadcast_address: str = "255.255.255.255"):
        """
        Initialize the transport layer with specified port and broadcast address.
        
        Args:
            port: UDP port to bind to (default: 50999 per RFC)
            broadcast_address: Network broadcast address (default: 255.255.255.255)
        """
        self.port = port
        self.broadcast_address = broadcast_address
        self.socket = None
        self.running = False
        self.receive_thread = None
        
        # Initialize the socket
        self._initialize_socket()
        
        logger.info(f"Transport initialized on port {port}")
    
    def _initialize_socket(self):
        """Create and configure the UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Allow socket reuse to avoid "address already in use" errors
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            self.socket.bind(("0.0.0.0", self.port))
            
            # Set up socket for broadcast
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Optional: increase buffer size for better performance with large messages
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            
            logger.debug("Socket initialized successfully")
            
        except Exception as e:
            logger.error(f"Socket initialization error: {e}")
            raise
    
    def send(self, message: bytes, address: Tuple[str, int]) -> bool:
        """
        Send a message to a specific address.
        
        Args:
            message: Encoded message bytes
            address: (ip, port) tuple
            
        Returns:
            Success status
        """
        try:
            self.socket.sendto(message, address)
            logger.debug(f"Sent {len(message)} bytes to {address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to {address}: {e}")
            return False
    
    def broadcast(self, message: bytes) -> bool:
        """
        Broadcast a message to the network.
        
        Args:
            message: Encoded message bytes
            
        Returns:
            Success status
        """
        try:
            # Send to broadcast address
            self.socket.sendto(message, (self.broadcast_address, self.port))
            logger.debug(f"Broadcast {len(message)} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return False
    
    def start_receiving(self, callback: Callable[[bytes, Tuple[str, int]], None]):
        """
        Start a background thread to receive messages.
        
        Args:
            callback: Function to call with received message and sender address
        """
        if self.running:
            logger.warning("Receive thread already running")
            return
            
        self.running = True
        
        def receive_loop():
            """Background thread to receive and process messages"""
            logger.info("Starting receive loop")
            
            while self.running:
                try:
                    # Buffer size set to handle large messages (e.g. with avatars)
                    data, addr = self.socket.recvfrom(1024 * 1024)
                    logger.debug(f"Received {len(data)} bytes from {addr}")
                    
                    # Process message in callback
                    callback(data, addr)
                    
                except socket.timeout:
                    # Socket timeout is normal, continue
                    pass
                except Exception as e:
                    if self.running:  # Only log if we're still meant to be running
                        logger.error(f"Error in receive loop: {e}")
                        # Brief pause to avoid tight loop if there's a persistent error
                        time.sleep(0.1)
            
            logger.info("Receive loop terminated")
        
        # Start the background thread
        self.receive_thread = threading.Thread(target=receive_loop, daemon=True)
        self.receive_thread.start()
        logger.info("Receive thread started")
    
    def stop_receiving(self):
        """Stop the receive thread"""
        if self.running:
            logger.info("Stopping receive thread...")
            self.running = False
            
            # Wait for thread to terminate (with timeout)
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)
                if self.receive_thread.is_alive():
                    logger.warning("Receive thread did not terminate gracefully")
            
            logger.info("Receive thread stopped")
    
    def close(self):
        """Close the socket and cleanup resources"""
        self.stop_receiving()
        
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket closed")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            
            self.socket = None
    
    def get_local_ip(self) -> str:
        """Get the local IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def set_socket_timeout(self, timeout: Optional[float]):
        """
        Set socket timeout for operations.
        
        Args:
            timeout: Timeout in seconds, or None for no timeout
        """
        if self.socket:
            try:
                self.socket.settimeout(timeout)
                logger.debug(f"Socket timeout set to {timeout}")
            except Exception as e:
                logger.error(f"Error setting socket timeout: {e}")