#!/usr/bin/env python3
"""
LSNP - Local Social Networking Protocol
Entry point for the peer-to-peer implementation
"""
import sys
import os
import argparse
import threading
import socket
import time
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import LSNP modules
from lsnp.protocol import Protocol
from lsnp.peer import Peer
from lsnp.discovery import start_discovery
from lsnp.transport import LSNPTransport
from lsnp.handler import MessageHandler
from config import DEFAULT_PORT, DEFAULT_TTL, BROADCAST_INTERVAL, VERSION

def setup_logging(verbose=False):
    """Configure logging based on verbosity level"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('lsnp')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="LSNP - Local Social Networking Protocol")
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                      help=f'Port to use (default: {DEFAULT_PORT})')
    parser.add_argument('-u', '--username', type=str,
                      help='Your username (will prompt if not provided)')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable verbose mode for detailed output')
    parser.add_argument('--avatar', type=str,
                      help='Path to avatar image file')
    parser.add_argument('--status', type=str, default="Hello from LSNP!",
                      help='Your status message')
    parser.add_argument('--broadcast-addr', type=str, default="255.255.255.255",
                      help='Broadcast address to use')
    return parser.parse_args()

def get_local_ip():
    """Get the local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    logger.info(f"Starting LSNP v{VERSION}")
    
    # Get username if not provided
    username = args.username if args.username else input("Enter your username: ")
    
    # Configure the local peer
    local_ip = get_local_ip()
    user_id = f"{username}@{local_ip}"
    logger.info(f"Local peer ID: {user_id}")
    
    # Initialize transport layer
    transport = LSNPTransport(args.port, args.broadcast_addr)
    
    # Initialize peer state
    peer = Peer(username, local_ip, args.status, args.port)
    
    # Initialize message handler
    handler = MessageHandler(transport, peer)
    
    # Start discovery service (sends periodic PING/PROFILE)
    discovery_thread = start_discovery(transport, peer, BROADCAST_INTERVAL)
    
    # Print welcome message
    print(f"\nLSNP Peer started - {username}@{local_ip}")
    print(f"Running on port {args.port}")
    print("Verbose mode: " + ("ON" if args.verbose else "OFF"))
    print("\nAvailable commands:")
    print("  POST <message>           - Send a message to everyone")
    print("  DM <user_id> <message>   - Send a direct message")
    print("  PROFILE                  - Update your profile")
    print("  LIST                     - List known peers")
    print("  FOLLOW <user_id>         - Follow a user")
    print("  UNFOLLOW <user_id>       - Unfollow a user")
    print("  FILE <user_id> <path>    - Send a file")
    print("  GROUP CREATE <name>      - Create a group")
    print("  GROUP JOIN <group_id>    - Join a group")
    print("  GROUP MSG <group_id> <msg> - Send a group message")
    print("  GAME <user_id>           - Invite to Tic Tac Toe")
    print("  VERBOSE                  - Toggle verbose mode")
    print("  HELP                     - Show this help")
    print("  EXIT                     - Exit the application")
    print("\nWaiting for peers to be discovered...")
    
    # If avatar provided, update profile with avatar
    if args.avatar and os.path.exists(args.avatar):
        handler.update_profile_with_avatar(args.avatar)
    else:
        # Send initial PROFILE broadcast
        handler.send_profile()
    
    # Start listening for incoming messages
    receive_thread = threading.Thread(target=transport.start_receiving, 
                                      args=(handler.handle_message,), 
                                      daemon=True)
    receive_thread.start()
    
    # Main command loop
    try:
        while True:
            cmd = input("> ")
            if not cmd:
                continue
                
            parts = cmd.split(maxsplit=1)
            command = parts[0].upper()
            
            if command == "EXIT":
                print("Shutting down...")
                break
                
            elif command == "HELP":
                print("\nAvailable commands:")
                print("  POST <message>           - Send a message to everyone")
                print("  DM <user_id> <message>   - Send a direct message")
                print("  PROFILE                  - Update your profile")
                print("  LIST                     - List known peers")
                print("  FOLLOW <user_id>         - Follow a user")
                print("  UNFOLLOW <user_id>       - Unfollow a user")
                print("  FILE <user_id> <path>    - Send a file")
                print("  GROUP CREATE <name>      - Create a group")
                print("  GROUP JOIN <group_id>    - Join a group")
                print("  GROUP MSG <group_id> <msg> - Send a group message")
                print("  GAME <user_id>           - Invite to Tic Tac Toe")
                print("  VERBOSE                  - Toggle verbose mode")
                print("  HELP                     - Show this help")
                print("  EXIT                     - Exit the application")
                
            elif command == "POST":
                if len(parts) < 2:
                    print("Usage: POST <message>")
                    continue
                content = parts[1]
                handler.send_post(content)
                
            elif command == "DM":
                if len(parts) < 2:
                    print("Usage: DM <user_id> <message>")
                    continue
                try:
                    recipient, message = parts[1].split(maxsplit=1)
                    handler.send_dm(recipient, message)
                except ValueError:
                    print("Usage: DM <user_id> <message>")
                    
            elif command == "LIST":
                known_peers = peer.get_known_peers()
                if not known_peers:
                    print("No peers discovered yet.")
                else:
                    print("\nKnown peers:")
                    for peer_id, peer_info in known_peers.items():
                        display_name = peer_info.get('display_name', peer_id)
                        status = peer_info.get('status', 'No status')
                        has_avatar = peer_info.get('has_avatar', False)
                        avatar_info = " [AVATAR]" if has_avatar else ""
                        print(f"  {display_name} ({peer_id}){avatar_info}: {status}")
                        
            elif command == "PROFILE":
                display_name = input("Display name (leave empty to keep current): ")
                status = input("Status message (leave empty to keep current): ")
                avatar_path = input("Avatar path (leave empty to keep current): ")
                
                if display_name or status or avatar_path:
                    if display_name:
                        peer.display_name = display_name
                    if status:
                        peer.status = status
                    if avatar_path and os.path.exists(avatar_path):
                        handler.update_profile_with_avatar(avatar_path)
                    else:
                        handler.send_profile()
                    print("Profile updated and broadcast to the network")
                else:
                    print("Profile unchanged")
                    
            elif command == "VERBOSE":
                # Toggle verbose mode
                args.verbose = not args.verbose
                logger = setup_logging(args.verbose)
                print(f"Verbose mode: {'ON' if args.verbose else 'OFF'}")
                
            elif command == "FOLLOW":
                if len(parts) < 2:
                    print("Usage: FOLLOW <user_id>")
                    continue
                user_to_follow = parts[1]
                handler.follow_user(user_to_follow)
                
            elif command == "UNFOLLOW":
                if len(parts) < 2:
                    print("Usage: UNFOLLOW <user_id>")
                    continue
                user_to_unfollow = parts[1]
                handler.unfollow_user(user_to_unfollow)
                
            elif command == "FILE":
                if len(parts) < 2:
                    print("Usage: FILE <user_id> <path>")
                    continue
                try:
                    recipient, file_path = parts[1].split(maxsplit=1)
                    if not os.path.exists(file_path):
                        print(f"File not found: {file_path}")
                        continue
                    handler.send_file(recipient, file_path)
                except ValueError:
                    print("Usage: FILE <user_id> <path>")
                    
            elif command == "GROUP" and len(parts) > 1:
                group_cmd = parts[1].split(maxsplit=2)
                if len(group_cmd) < 2:
                    print("Usage: GROUP <CREATE|JOIN|MSG> ...")
                    continue
                
                group_action = group_cmd[0].upper()
                if group_action == "CREATE" and len(group_cmd) >= 2:
                    group_name = group_cmd[1]
                    handler.create_group(group_name)
                elif group_action == "JOIN" and len(group_cmd) >= 2:
                    group_id = group_cmd[1]
                    handler.join_group(group_id)
                elif group_action == "MSG" and len(group_cmd) >= 3:
                    group_id = group_cmd[1]
                    message = group_cmd[2]
                    handler.send_group_message(group_id, message)
                else:
                    print("Usage: GROUP <CREATE|JOIN|MSG> ...")
                    
            elif command == "GAME":
                if len(parts) < 2:
                    print("Usage: GAME <user_id>")
                    continue
                opponent = parts[1]
                handler.invite_to_game(opponent)
                
            else:
                print(f"Unknown command: {command}")
                print("Type HELP for available commands")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    # Clean shutdown
    transport.close()
    print("Goodbye!")
    
if __name__ == "__main__":
    main()