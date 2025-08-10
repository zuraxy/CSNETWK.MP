#!/usr/bin/env python3
"""
Main Peer Launcher
Starts a P2P peer using the modular architecture
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the modular peer
from peer.core.peer_core import main

if __name__ == "__main__":
    main()
