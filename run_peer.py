#!/usr/bin/env python3
"""
Launcher script for UDP Peer (Modular Architecture)
Run this from the root directory to start a peer in the P2P network
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the modular peer
if __name__ == "__main__":
    from peer.core.peer_core import main
    print("=" * 60)
    print("UDP PEER-TO-PEER CHAT (MODULAR ARCHITECTURE)")
    print("=" * 60)
    print("🌐 Serverless P2P Implementation")
    print("📡 Automatic peer discovery via broadcast")
    print("💬 Direct peer-to-peer communication")
    print("🔍 No central server required")
    print("🔧 Clean modular architecture")
    print("=" * 60)
    
    print("""
Key Features:
- POST: Broadcast messages to all discovered peers
- DM: Send direct messages to specific peers  
- PROFILE: Share your profile (with optional avatar) with all peers
- LIST: Show all discovered peers on the network
- GROUP: Create and manage group chats with multiple users
- VERBOSE: Toggle between technical and user-friendly display
- QUIT: Exit the application

Group Chat Features:
- Create groups with multiple members
- Send messages to all group members
- Add/remove members from groups (creator only)
- View group information and membership
- List all groups you belong to
- Leave groups you no longer want to be part of

Peer Discovery:
- Peers automatically discover each other via UDP broadcast
- Uses port 50999 for discovery announcements
- Each peer listens on a random port (8000-9999)
- Peers are removed after 5 minutes of inactivity

Getting Started:
1. Start multiple instances of this script on the same network
2. Wait a few seconds for peer discovery to work
3. Use LIST command to see discovered peers
4. Start chatting with POST and DM commands!
""")
    
    try:
        main()
    except Exception as e:
        print(f"Fatal error in main: {e}")
    # No need to call shutdown explicitly - it's handled in the main() function
