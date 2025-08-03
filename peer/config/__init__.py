"""
Configuration Package
Provides centralized configuration settings for the P2P system
"""

# Import common settings for easier access
from .settings import (
    DISCOVERY_PORT,
    PEER_PORT_RANGE,
    SOCKET_BUFFER_SIZE,
    BROADCAST_ADDRESSES,
    DISCOVERY_INTERVAL,
    PEER_TIMEOUT,
    DEFAULT_VERBOSE_MODE,
    DEFAULT_SCAN_TIMEOUT
)

# Define what gets imported with "from peer.config import *"
__all__ = [
    'DISCOVERY_PORT',
    'PEER_PORT_RANGE',
    'SOCKET_BUFFER_SIZE',
    'BROADCAST_ADDRESSES',
    'DISCOVERY_INTERVAL',
    'PEER_TIMEOUT',
    'DEFAULT_VERBOSE_MODE',
    'DEFAULT_SCAN_TIMEOUT'
]