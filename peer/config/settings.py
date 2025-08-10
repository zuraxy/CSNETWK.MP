"""
Centralized Configuration Module
Contains all configurable parameters for the P2P system
"""
import os

# Network settings
DISCOVERY_PORT = 51000  # Changed from 50999 to avoid conflicts
PEER_PORT_RANGE = (8000, 9999)
SOCKET_BUFFER_SIZE = 65536
BROADCAST_ADDRESSES = ['255.255.255.255', '127.0.0.1', '192.168.1.255', '10.0.0.255']  # Added more broadcast addresses

# Peer management settings
DISCOVERY_INTERVAL = 5   # Reduced from 30 to 5 seconds for faster discovery
PEER_TIMEOUT = 60        # Reduced from 300 to 60 seconds for testing

# User interface settings
DEFAULT_VERBOSE_MODE = True

# Discovery settings
DEFAULT_SCAN_TIMEOUT = 5  # Seconds

# Profile settings
AVATAR_MAX_SIZE = 20 * 1024  # 20KB

# File paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))