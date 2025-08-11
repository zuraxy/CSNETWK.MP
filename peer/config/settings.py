"""
Centralized Configuration Module
Contains all configurable parameters for the P2P system
"""
import os

# Network settings
DISCOVERY_PORT = 50999
PEER_PORT_RANGE = (8000, 9999)
SOCKET_BUFFER_SIZE = 65536
BROADCAST_ADDRESSES = ['255.255.255.255', '127.0.0.1']

# Peer management settings
DISCOVERY_INTERVAL = 30  # Seconds between discovery broadcasts
PEER_TIMEOUT = 300       # Seconds before considering a peer offline (5 minutes)

# User interface settings
DEFAULT_VERBOSE_MODE = True

# Discovery settings
DEFAULT_SCAN_TIMEOUT = 5  # Seconds

# Profile settings
AVATAR_MAX_SIZE = 20 * 1024  # 20KB

# File paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TTL settings (in seconds)
DEFAULT_POST_TTL = 3600   
TTL_CLEANUP_INTERVAL = 60   