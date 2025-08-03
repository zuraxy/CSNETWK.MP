#!/usr/bin/env python3
"""
UDP Peer-to-Peer Implementation
No central server - peers communicate directly with each other
"""
import socket
import threading
import random
import secrets
import time
import sys
import os
import base64
import mimetypes
import json

# Add the parent directory to Python path to access protocol module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

encode_message = Protocol.encode_message
decode_message = Protocol.decode_message

class UDPPeer:
    def __init__(self):
        # Network configuration
        self.local_port = random.randint(8000, 9999)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcast
        self.socket.bind(("", self.local_port))
        
        # Discovery socket - listens on broadcast port for peer announcements
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.discovery_socket.bind(("", 50999))
            self.has_discovery_socket = True
            print(f"Discovery socket bound to port 50999")
        except Exception as e:
            print(f"Warning: Could not bind discovery socket to port 50999: {e}")
            print(f"Discovery will use main socket only")
            self.has_discovery_socket = False
        
        # Peer information
        self.username = ""
        self.local_ip = self.get_local_ip()
        self.user_id = ""
        
        # Peer discovery and tracking
        self.known_peers = {}  # user_id -> {'ip': str, 'port': int, 'last_seen': timestamp}
        self.user_profiles = {}  # user_id -> {'display_name': str, 'avatar': bool, 'avatar_type': str}
        
        # UI configuration
        self.verbose_mode = True
        
        # Network discovery
        self.broadcast_port = 50999  # Port for peer discovery broadcasts
        self.discovery_interval = 30  # Seconds between discovery broadcasts
        
        print(f"Peer initialized on {self.local_ip}:{self.local_port}")
    
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a dummy address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def generate_message_id(self):
        """Generate a unique message ID"""
        return secrets.token_hex(8)
    
    def start(self):
        """Start the peer and all its threads"""
        # Get user information
        self.username = input("Username: ")
        self.user_id = f"{self.username}@{self.local_ip}"
        
        # Verbose mode setting
        verbose_input = input("Enable verbose mode? (y/n, default=y): ").strip().lower()
        self.verbose_mode = verbose_input != 'n'
        print(f"Verbose mode: {'ON' if self.verbose_mode else 'OFF'}")
        
        print(f"Peer started as {self.user_id}")
        print(f"Listening on {self.local_ip}:{self.local_port}")
        
        # Start background threads
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        # Start discovery listener thread if we have discovery socket
        if self.has_discovery_socket:
            discovery_receive_thread = threading.Thread(target=self.receive_discovery_messages)
            discovery_receive_thread.daemon = True
            discovery_receive_thread.start()
        
        discovery_thread = threading.Thread(target=self.peer_discovery)
        discovery_thread.daemon = True
        discovery_thread.start()
        
        # Initial peer discovery
        self.announce_presence()
        
        # Start main command loop
        self.command_loop()
    
    def receive_messages(self):
        """Continuously listen for incoming messages"""
        while True:
            try:
                data, addr = self.socket.recvfrom(65536)
                self.handle_incoming_message(data, addr)
            except Exception as e:
                if self.verbose_mode:
                    print(f"Error receiving message: {e}")
    
    def receive_discovery_messages(self):
        """Listen for discovery broadcasts on port 50999"""
        while True:
            try:
                data, addr = self.discovery_socket.recvfrom(65536)
                self.handle_incoming_message(data, addr)
            except Exception as e:
                if self.verbose_mode:
                    print(f"Error receiving discovery message: {e}")
    
    def handle_incoming_message(self, data, addr):
        """Process incoming messages from other peers"""
        try:
            # Try to decode as protocol message
            msg_dict = decode_message(data)
            msg_type = msg_dict.get('TYPE', '')
            
            # Update peer information
            sender_id = msg_dict.get('USER_ID') or msg_dict.get('FROM', '')
            if sender_id and sender_id != self.user_id:
                self.update_peer_info(sender_id, addr[0], addr[1])
            
            if msg_type == 'PEER_DISCOVERY':
                self.handle_peer_discovery(msg_dict, addr)
            elif msg_type == 'POST':
                self.handle_post_message(msg_dict)
            elif msg_type == 'DM':
                self.handle_dm_message(msg_dict)
            elif msg_type == 'PROFILE':
                self.handle_profile_message(msg_dict)
            elif msg_type == 'PEER_LIST_REQUEST':
                self.handle_peer_list_request(msg_dict, addr)
            elif msg_type == 'PEER_LIST_RESPONSE':
                self.handle_peer_list_response(msg_dict)
            else:
                if self.verbose_mode:
                    print(f"Unknown message type: {msg_type}")
                    
        except Exception as e:
            if self.verbose_mode:
                print(f"Error processing message from {addr}: {e}")
    
    def handle_peer_discovery(self, msg_dict, addr):
        """Handle peer discovery announcements"""
        sender_id = msg_dict.get('USER_ID', '')
        if sender_id and sender_id != self.user_id:
            self.update_peer_info(sender_id, addr[0], msg_dict.get('PORT', addr[1]))
            
            if self.verbose_mode:
                print(f"[DISCOVERY] Found peer: {sender_id}")
            
            # Respond with our own presence
            self.send_discovery_response(addr[0], int(msg_dict.get('PORT', addr[1])))
    
    def handle_post_message(self, msg_dict):
        """Handle broadcast POST messages"""
        user_id = msg_dict.get('USER_ID', 'Unknown')
        content = msg_dict.get('CONTENT', '')
        
        if self.verbose_mode:
            print(f"\n[POST] {user_id}: {content}")
        else:
            display_name = self.get_display_name(user_id)
            avatar_info = self.get_avatar_info(user_id)
            print(f"\n{display_name}{avatar_info}: {content}")
    
    def handle_dm_message(self, msg_dict):
        """Handle direct messages"""
        from_user = msg_dict.get('FROM', 'Unknown')
        to_user = msg_dict.get('TO', '')
        content = msg_dict.get('CONTENT', '')
        
        # Only display if this message is for us
        if to_user == self.user_id:
            if self.verbose_mode:
                print(f"\n[DM] From {from_user}: {content}")
            else:
                display_name = self.get_display_name(from_user)
                avatar_info = self.get_avatar_info(from_user)
                print(f"\n{display_name}{avatar_info}: {content}")
    
    def handle_profile_message(self, msg_dict):
        """Handle profile update messages"""
        user_id = msg_dict.get('USER_ID', 'Unknown')
        display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
        status = msg_dict.get('STATUS', '')
        has_avatar = 'AVATAR_DATA' in msg_dict
        avatar_type = msg_dict.get('AVATAR_TYPE', '')
        
        # Update our profile storage
        self.update_user_profile(user_id, display_name, has_avatar, avatar_type)
        
        if self.verbose_mode:
            print(f"\n[PROFILE UPDATE] {display_name} ({user_id})")
            print(f"  Status: {status}")
            if has_avatar:
                print(f"  Avatar: {avatar_type} (base64 encoded)")
        else:
            print(f"\n{display_name}")
            print(f"   {status}")
    
    def handle_peer_list_request(self, msg_dict, addr):
        """Handle requests for peer list"""
        requester = msg_dict.get('FROM', '')
        if requester and requester != self.user_id:
            # Send our known peers back to requester
            peer_list = list(self.known_peers.keys())
            response = {
                'TYPE': 'PEER_LIST_RESPONSE',
                'FROM': self.user_id,
                'PEERS': json.dumps(peer_list),
                'COUNT': str(len(peer_list)),
                'TIMESTAMP': str(int(time.time())),
                'MESSAGE_ID': self.generate_message_id()
            }
            self.send_to_address(encode_message(response), addr[0], addr[1])
    
    def handle_peer_list_response(self, msg_dict):
        """Handle peer list responses"""
        try:
            peers = json.loads(msg_dict.get('PEERS', '[]'))
            count = msg_dict.get('COUNT', '0')
            
            if self.verbose_mode:
                print(f"\n[PEER LIST] ({count} peers): {', '.join(peers)}")
            else:
                display_names = [self.get_display_name(peer) for peer in peers]
                print(f"\nOnline ({count}): {', '.join(display_names)}")
        except:
            print("\n[ERROR] Could not parse peer list")
    
    def update_peer_info(self, user_id, ip, port):
        """Update information about a known peer"""
        self.known_peers[user_id] = {
            'ip': ip,
            'port': int(port),
            'last_seen': time.time()
        }
    
    def update_user_profile(self, user_id, display_name=None, has_avatar=False, avatar_type=''):
        """Update stored user profile information"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {'display_name': '', 'avatar': False, 'avatar_type': ''}
        
        if display_name:
            self.user_profiles[user_id]['display_name'] = display_name
        self.user_profiles[user_id]['avatar'] = has_avatar
        self.user_profiles[user_id]['avatar_type'] = avatar_type
    
    def get_display_name(self, user_id):
        """Get display name for a user, fallback to user_id if not available"""
        if user_id in self.user_profiles and self.user_profiles[user_id]['display_name']:
            return self.user_profiles[user_id]['display_name']
        return user_id
    
    def get_avatar_info(self, user_id):
        """Get avatar information for a user"""
        if user_id in self.user_profiles and self.user_profiles[user_id]['avatar']:
            return f"({self.user_profiles[user_id]['avatar_type']})"
        return ""
    
    def peer_discovery(self):
        """Periodically announce presence to discover other peers"""
        while True:
            time.sleep(self.discovery_interval)
            self.announce_presence()
            self.cleanup_old_peers()
    
    def announce_presence(self):
        """Broadcast presence announcement to discover peers"""
        try:
            announcement = {
                'TYPE': 'PEER_DISCOVERY',
                'USER_ID': self.user_id,
                'PORT': str(self.local_port),
                'TIMESTAMP': str(int(time.time())),
                'MESSAGE_ID': self.generate_message_id()
            }
            
            # Broadcast to local network
            self.socket.sendto(encode_message(announcement), ('255.255.255.255', self.broadcast_port))
            self.socket.sendto(encode_message(announcement), ('127.0.0.1', self.broadcast_port))
            
            if self.verbose_mode:
                print(f"[DISCOVERY] Announced presence as {self.user_id}")
                
        except Exception as e:
            if self.verbose_mode:
                print(f"Error announcing presence: {e}")
    
    def send_discovery_response(self, target_ip, target_port):
        """Send discovery response to a specific peer"""
        try:
            response = {
                'TYPE': 'PEER_DISCOVERY',
                'USER_ID': self.user_id,
                'PORT': str(self.local_port),
                'TIMESTAMP': str(int(time.time())),
                'MESSAGE_ID': self.generate_message_id()
            }
            self.send_to_address(encode_message(response), target_ip, target_port)
        except Exception as e:
            if self.verbose_mode:
                print(f"Error sending discovery response: {e}")
    
    def cleanup_old_peers(self):
        """Remove peers that haven't been seen recently"""
        current_time = time.time()
        timeout = 300  # 5 minutes timeout
        
        old_peers = []
        for user_id, peer_info in self.known_peers.items():
            if current_time - peer_info['last_seen'] > timeout:
                old_peers.append(user_id)
        
        for user_id in old_peers:
            del self.known_peers[user_id]
            if self.verbose_mode:
                print(f"[CLEANUP] Removed inactive peer: {user_id}")
    
    def send_to_address(self, data, ip, port):
        """Send data to a specific address"""
        try:
            self.socket.sendto(data, (ip, port))
        except Exception as e:
            if self.verbose_mode:
                print(f"Error sending to {ip}:{port}: {e}")
    
    def broadcast_to_peers(self, data):
        """Send data to all known peers"""
        sent_count = 0
        for user_id, peer_info in self.known_peers.items():
            try:
                self.send_to_address(data, peer_info['ip'], peer_info['port'])
                sent_count += 1
            except Exception as e:
                if self.verbose_mode:
                    print(f"Error sending to {user_id}: {e}")
        return sent_count
    
    def send_to_specific_peer(self, data, target_user_id):
        """Send data to a specific peer"""
        if target_user_id in self.known_peers:
            peer_info = self.known_peers[target_user_id]
            self.send_to_address(data, peer_info['ip'], peer_info['port'])
            return True
        return False
    
    def command_loop(self):
        """Main command processing loop"""
        print(f"\nPeer-to-Peer Chat Ready!")
        print(f"Commands: POST, DM, PROFILE, LIST, VERBOSE, QUIT")
        
        while True:
            try:
                cmd = input("\nCommand (POST/DM/PROFILE/LIST/VERBOSE/QUIT): ").strip().upper()
                
                if cmd == "QUIT":
                    print("Goodbye!")
                    break
                elif cmd == "VERBOSE":
                    self.verbose_mode = not self.verbose_mode
                    print(f"Verbose mode: {'ON' if self.verbose_mode else 'OFF'}")
                elif cmd == "POST":
                    self.handle_post_command()
                elif cmd == "DM":
                    self.handle_dm_command()
                elif cmd == "PROFILE":
                    self.handle_profile_command()
                elif cmd == "LIST":
                    self.handle_list_command()
                else:
                    print("Invalid command. Use POST, DM, PROFILE, LIST, VERBOSE, or QUIT")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def handle_post_command(self):
        """Handle POST (broadcast message) command"""
        message = input("Message: ")
        
        data = {
            'TYPE': 'POST',
            'USER_ID': self.user_id,
            'CONTENT': message,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self.generate_message_id()
        }
        
        encoded_data = encode_message(data)
        sent_count = self.broadcast_to_peers(encoded_data)
        
        if self.verbose_mode:
            print(f"Message broadcasted to {sent_count} peers")
    
    def handle_dm_command(self):
        """Handle DM (direct message) command"""
        if not self.known_peers:
            print("No peers available. Use LIST to discover peers first.")
            return
        
        print("Available peers:")
        for user_id in self.known_peers.keys():
            display_name = self.get_display_name(user_id)
            print(f"  - {user_id} ({display_name})")
        
        recipient = input("Recipient (user@ip): ").strip()
        if not recipient:
            print("No recipient specified")
            return
        
        message = input("Message: ")
        
        data = {
            'TYPE': 'DM',
            'FROM': self.user_id,
            'TO': recipient,
            'CONTENT': message,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self.generate_message_id()
        }
        
        encoded_data = encode_message(data)
        if self.send_to_specific_peer(encoded_data, recipient):
            if self.verbose_mode:
                print(f"DM sent to {recipient}")
        else:
            print(f"Error: Peer {recipient} not found or unreachable")
    
    def handle_profile_command(self):
        """Handle PROFILE command"""
        display_name = input("Display Name: ").strip()
        if not display_name:
            display_name = self.username
        
        status = input("Status message: ").strip()
        if not status:
            status = "Hello from P2P LSNP!"
        
        add_avatar = input("Add profile picture? (y/n): ").strip().lower() == 'y'
        
        data = {
            'TYPE': 'PROFILE',
            'USER_ID': self.user_id,
            'DISPLAY_NAME': display_name,
            'STATUS': status,
            'TIMESTAMP': str(int(time.time())),
            'MESSAGE_ID': self.generate_message_id()
        }
        
        if add_avatar:
            avatar_path = input("Enter path to image file (or press Enter to skip): ").strip()
            if avatar_path and os.path.exists(avatar_path):
                try:
                    file_size = os.path.getsize(avatar_path)
                    if file_size > 20480:  # 20KB
                        print(f"Warning: File size ({file_size} bytes) is larger than recommended 20KB")
                        continue_anyway = input("Continue anyway? (y/n): ").strip().lower() == 'y'
                        if not continue_anyway:
                            print("Avatar upload cancelled")
                            add_avatar = False
                    
                    if add_avatar:
                        with open(avatar_path, 'rb') as f:
                            avatar_bytes = f.read()
                            avatar_b64 = base64.b64encode(avatar_bytes).decode('utf-8')
                            
                            mime_type, _ = mimetypes.guess_type(avatar_path)
                            if not mime_type or not mime_type.startswith('image/'):
                                mime_type = 'image/png'
                            
                            data['AVATAR_TYPE'] = mime_type
                            data['AVATAR_ENCODING'] = 'base64'
                            data['AVATAR_DATA'] = avatar_b64
                            print(f"Avatar added: {mime_type}, {len(avatar_b64)} characters")
                            
                except Exception as e:
                    print(f"Error reading avatar file: {e}")
            elif avatar_path:
                print(f"File not found: {avatar_path}")
        
        # Update our own profile
        has_avatar = 'AVATAR_DATA' in data
        self.update_user_profile(self.user_id, display_name, has_avatar, data.get('AVATAR_TYPE', ''))
        
        # Broadcast profile to all peers
        encoded_data = encode_message(data)
        sent_count = self.broadcast_to_peers(encoded_data)
        
        print(f"Profile updated and broadcasted to {sent_count} peers")
    
    def handle_list_command(self):
        """Handle LIST command to show known peers"""
        if not self.known_peers:
            print("No peers discovered yet. Wait for peer discovery or try again.")
            # Send discovery request
            self.announce_presence()
            return
        
        if self.verbose_mode:
            print(f"\n[KNOWN PEERS] ({len(self.known_peers)} peers):")
            for user_id, peer_info in self.known_peers.items():
                last_seen = int(time.time() - peer_info['last_seen'])
                print(f"  - {user_id} ({peer_info['ip']}:{peer_info['port']}) [seen {last_seen}s ago]")
        else:
            peer_names = [self.get_display_name(user_id) for user_id in self.known_peers.keys()]
            print(f"\nKnown Peers ({len(self.known_peers)}): {', '.join(peer_names)}")

def main():
    """Main function to start the peer"""
    peer = UDPPeer()
    try:
        peer.start()
    except KeyboardInterrupt:
        print("\nShutting down peer...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
