#!/usr/bin/env python3
"""
Launcher script for UDP Client
Run this from the root directory to start the client
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the client
if __name__ == "__main__":
    from client.udp_client import *
    print("UDP Client started")
    print("""Client Features:
    - Verbose Mode: Choose ON for technical details, OFF for clean display
    - Commands: POST, DM, PROFILE, LIST, VERBOSE (toggle)
    - Non-verbose shows display names and avatars when available
    - Use VERBOSE command anytime to toggle between modes""")
