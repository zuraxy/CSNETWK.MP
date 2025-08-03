#!/usr/bin/env python3
"""
Launcher script for UDP Server
Run this from the root directory to start the server
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # since this is run_server, we want 0 so that python first searches/indexes this file's directory. In short, kinda just adds to path - priority 0

# Import and run the server
if __name__ == "__main__":
    from server.udp_server import *
    print("UDP Server started on localhost:50999\n")
    print("""Usage instructions:
    1. After starting the server with: python run_server.py
    2. Start client(s): python run_client.py [*do this with how many clients you want to make.] 
    3. Use 'POST' command to broadcast messages
    4. Use 'DM' command to send direct messages
    5. Use 'PROFILE' command to create/update your profile (with optional avatar)
    6. Use 'LIST' command to see online users""")
