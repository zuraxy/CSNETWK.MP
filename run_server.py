#!/usr/bin/env python3
"""
Launcher script for UDP Server
Run this from the root directory to start the server
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the server
if __name__ == "__main__":
    from server.udp_server import *
    print("UDP Server started on localhost:50999")
