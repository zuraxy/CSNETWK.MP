import cmd
import os
import sys
import time
import logging
import socket
import threading
from typing import Optional, List, Dict

# Import LSNP modules
from lsnp.peer import Peer
from lsnp.transport import LSNPTransport
from lsnp.handler import MessageHandler
from lsnp.protocol import Protocol
from lsnp.discovery import start_discovery, schedule_cleanup
from lsnp.game import GameManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('lsnp.log')
    ]
)
logger = logging.getLogger('lsnp.cli')


class LSNPInterface(cmd.Cmd):
    """
    Command-line interface for the LSNP protocol.
    Provides commands for peer discovery, messaging, and other LSNP features.
    """
    
    intro = """
    ╔════════════════════════════════════════════════╗
    ║           LSNP Peer-to-Peer Network            ║
    ║                                                ║
    ║ Type 'help' for a list of commands             ║
    ║ Type 'start' to join the network               ║
    ║                                                ║
    ╚════════════════════════════════════════════════╝
    """
    prompt = 'lsnp> '
    
    def __init__(self, username: str = None):
        """Initialize the interface"""
        super().__init__()
        
        self.username = username or self.get_username()
        self.transport = None
        self.peer = None
        self.handler = None
        self.game_manager = None
        self.discovery_thread = None
        self.cleanup_thread = None
        self.running = False
        
        # Thread for receiving and handling messages
        self.receive_thread = None
        
        # Verbose mode for debugging
        self.verbose_mode = False
        
    def get_username(self) -> str:
        """Prompt for username if not provided"""
        while True:
            username = input("Enter your username (alphanumeric only): ")
            if username and username.replace("_", "").isalnum():
                return username
            print("Invalid username. Please use only letters, numbers, and underscores.")
    
    def get_ip_address(self) -> str:
        """Get local IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def initialize_components(self):
        """Initialize all LSNP components"""
        try:
            ip_address = self.get_ip_address()
            
            # Initialize transport
            self.transport = LSNPTransport()
            
            # Initialize peer
            self.peer = Peer(
                username=self.username,
                ip_address=ip_address,
                port=self.transport.port
            )
            
            # Initialize message handler
            self.handler = MessageHandler(self.transport, self.peer)
            
            # Initialize game manager
            self.game_manager = GameManager(self.peer.user_id)
            
            print(f"Initialized peer: {self.peer.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def start_network(self):
        """Start network services"""
        if self.running:
            print("Network already running.")
            return
            
        # Start message receiving
        def receive_callback(data, addr):
            try:
                if self.verbose_mode:
                    print(f"\nReceived {len(data)} bytes from {addr}")
                self.handler.handle_message(data, addr)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        self.transport.start_receiving(receive_callback)
        
        # Start discovery
        self.discovery_thread = start_discovery(self.transport, self.peer)
        
        # Start cleanup
        self.cleanup_thread = schedule_cleanup(self.peer)
        
        self.running = True
        print("Network services started. Broadcasting presence...")
        
        # Send initial profile
        self.handler.send_profile()
    
    def stop_network(self):
        """Stop network services"""
        if not self.running:
            print("Network not running.")
            return
            
        # Stop transport
        if self.transport:
            self.transport.stop_receiving()
            self.transport.close()
        
        self.running = False
        print("Network services stopped.")
    
    def do_start(self, arg):
        """Start LSNP network services and join the network."""
        if not self.transport:
            if not self.initialize_components():
                print("Failed to initialize. Check log for details.")
                return
                
        self.start_network()
        print(f"Joined the network as {self.peer.user_id}")
        print("Use 'help' to see available commands.")
    
    def do_stop(self, arg):
        """Stop LSNP network services and leave the network."""
        self.stop_network()
    
    def do_profile(self, arg):
        """
        Set or view your profile information.
        Usage: profile [display_name] [status]
        Example: profile "John Doe" "Hello, world!"
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        if not arg:
            # Display current profile
            print(f"Username: {self.peer.username}")
            print(f"User ID: {self.peer.user_id}")
            print(f"Display name: {self.peer.display_name}")
            print(f"Status: {self.peer.status}")
            print(f"Avatar: {'Yes' if self.peer.has_avatar else 'No'}")
            return
            
        # Parse arguments
        parts = arg.split('"')
        if len(parts) >= 3:
            # Extract quoted display name
            display_name = parts[1]
            
            # Try to extract status if provided
            status = None
            if len(parts) >= 5:
                status = parts[3]
        else:
            # Simple space-separated format
            args = arg.split()
            if len(args) >= 1:
                display_name = args[0]
                status = " ".join(args[1:]) if len(args) > 1 else None
            else:
                print("Invalid arguments. Usage: profile [display_name] [status]")
                return
        
        # Update profile
        if display_name or status:
            self.peer.update_profile(display_name=display_name, status=status)
            print("Profile updated.")
            
            # Broadcast updated profile
            if self.running:
                self.handler.send_profile()
                print("Profile broadcast to network.")
    
    def do_avatar(self, arg):
        """
        Set your avatar image.
        Usage: avatar path/to/image.jpg
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        if not arg:
            print("Please provide the path to an image file.")
            return
            
        # Check if file exists
        if not os.path.exists(arg):
            print(f"File not found: {arg}")
            return
            
        # Update avatar and broadcast
        if self.running:
            success = self.handler.update_profile_with_avatar(arg)
            if success:
                print("Avatar updated and broadcast to network.")
            else:
                print("Failed to update avatar. Check log for details.")
        else:
            self.peer.update_profile(avatar_path=arg)
            print("Avatar updated. Will be broadcast when you start the network.")
    
    def do_peers(self, arg):
        """
        List all known peers on the network.
        Usage: peers
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        peers = self.peer.get_known_peers()
        
        if not peers:
            print("No peers discovered yet.")
            return
            
        print(f"\nDiscovered peers: {len(peers)}")
        print("=" * 60)
        print(f"{'User ID':<30} {'Display Name':<20} {'Status'}")
        print("-" * 60)
        
        for user_id, info in peers.items():
            display_name = info.get('display_name', 'Unknown')
            status = info.get('status', '')
            print(f"{user_id:<30} {display_name:<20} {status}")
    
    def do_follow(self, arg):
        """
        Follow a peer.
        Usage: follow user_id
        Example: follow alice@192.168.1.100
        """
        if not self.running:
            print("Please start the network first with 'start'.")
            return
            
        if not arg:
            print("Please provide a user ID to follow.")
            return
            
        success = self.handler.follow_user(arg)
        
        if success:
            print(f"Now following: {arg}")
        else:
            print(f"Failed to follow {arg}. Check if the user exists.")
    
    def do_unfollow(self, arg):
        """
        Unfollow a peer.
        Usage: unfollow user_id
        Example: unfollow alice@192.168.1.100
        """
        if not self.running:
            print("Please start the network first with 'start'.")
            return
            
        if not arg:
            print("Please provide a user ID to unfollow.")
            return
            
        success = self.handler.unfollow_user(arg)
        
        if success:
            print(f"Unfollowed: {arg}")
        else:
            print(f"Failed to unfollow {arg}. Check if you were following this user.")
    
    def do_following(self, arg):
        """
        List all peers you are following.
        Usage: following
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        following = self.peer.following
        
        if not following:
            print("You are not following anyone.")
            return
            
        print(f"\nFollowing: {len(following)}")
        print("=" * 60)
        print(f"{'User ID':<30} {'Display Name':<20}")
        print("-" * 60)
        
        for user_id in following:
            display_name = self.peer.get_display_name(user_id)
            print(f"{user_id:<30} {display_name:<20}")
    
    def do_followers(self, arg):
        """
        List all peers following you.
        Usage: followers
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        followers = self.peer.followers
        
        if not followers:
            print("You have no followers.")
            return
            
        print(f"\nFollowers: {len(followers)}")
        print("=" * 60)
        print(f"{'User ID':<30} {'Display Name':<20}")
        print("-" * 60)
        
        for user_id in followers:
            display_name = self.peer.get_display_name(user_id)
            print(f"{user_id:<30} {display_name:<20}")
    
    def do_post(self, arg):
        """
        Create a new post.
        Usage: post Your post content here
        """
        if not self.running:
            print("Please start the network first with 'start'.")
            return
            
        if not arg:
            print("Please provide content for your post.")
            return
            
        success = self.handler.send_post(arg)
        
        if success:
            print("Post sent to the network.")
        else:
            print("Failed to send post. Check log for details.")
    
    def do_timeline(self, arg):
        """
        View posts from you and peers you follow.
        Usage: timeline [count]
        Example: timeline 10
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        count = 10  # Default
        if arg:
            try:
                count = int(arg)
            except ValueError:
                print("Invalid count. Using default (10).")
        
        posts = self.peer.posts
        if not posts:
            print("No posts in your timeline.")
            return
            
        # Sort by timestamp (newest first)
        sorted_posts = sorted(
            posts.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        print("\nTimeline:")
        print("=" * 60)
        
        shown = 0
        for message_id, post in sorted_posts:
            if shown >= count:
                break
                
            user_id = post['user_id']
            content = post['content']
            timestamp = post['timestamp']
            
            # Format timestamp
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
            
            # Get display name
            display_name = self.peer.get_display_name(user_id)
            
            print(f"{display_name} ({user_id}) - {time_str}")
            print(f"{content}")
            print("-" * 60)
            
            shown += 1
            
        if shown == 0:
            print("No posts in your timeline.")
    
    def do_dm(self, arg):
        """
        Send a direct message to a peer.
        Usage: dm user_id Message content goes here
        Example: dm alice@192.168.1.100 Hello Alice!
        """
        if not self.running:
            print("Please start the network first with 'start'.")
            return
            
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: dm user_id Message content")
            return
            
        recipient, content = parts
        
        success = self.handler.send_dm(recipient, content)
        
        if success:
            print(f"DM sent to {recipient}.")
        else:
            print(f"Failed to send DM. Check if the user exists.")
    
    def do_messages(self, arg):
        """
        View your direct messages.
        Usage: messages [received|sent]
        """
        if not self.peer:
            print("Please start the network first with 'start'.")
            return
            
        mode = "received"
        if arg:
            if arg in ["received", "sent"]:
                mode = arg
            else:
                print("Invalid option. Use 'received' or 'sent'.")
                return
        
        if mode == "received":
            messages = self.peer.dms_received
            title = "Received Messages"
        else:
            messages = self.peer.dms_sent
            title = "Sent Messages"
            
        if not messages:
            print(f"No {mode} messages.")
            return
            
        # Sort by timestamp (newest first)
        sorted_messages = sorted(
            messages.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        print(f"\n{title}:")
        print("=" * 60)
        
        for message_id, message in sorted_messages:
            if mode == "received":
                user_id = message['from']
                label = "From"
            else:
                user_id = message['to']
                label = "To"
                
            content = message['content']
            timestamp = message['timestamp']
            
            # Format timestamp
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
            
            # Get display name
            display_name = self.peer.get_display_name(user_id)
            
            print(f"{label}: {display_name} ({user_id}) - {time_str}")
            print(f"{content}")
            print("-" * 60)
    
    def do_game(self, arg):
        """
        Manage Tic-Tac-Toe games.
        Usage:
          game invite user_id - Invite a user to play
          game accept game_id - Accept a game invitation
          game reject game_id - Reject a game invitation
          game list - List active games
          game show game_id - Show game state
          game move game_id row col - Make a move (0-2)
        """
        if not self.running:
            print("Please start the network first with 'start'.")
            return
            
        parts = arg.split()
        if not parts:
            print("Please provide a game command.")
            self.help_game()
            return
            
        command = parts[0].lower()
        
        if command == "invite" and len(parts) > 1:
            opponent = parts[1]
            # Implementation would call handler.invite_to_game(opponent)
            print("Game invitations not fully implemented")
            
        elif command == "accept" and len(parts) > 1:
            game_id = parts[1]
            # Implementation would call game_manager.accept_invitation(game_id)
            print("Game acceptance not fully implemented")
            
        elif command == "reject" and len(parts) > 1:
            game_id = parts[1]
            # Implementation would call game_manager.reject_invitation(game_id)
            print("Game rejection not fully implemented")
            
        elif command == "list":
            # Implementation would list active games
            print("Game listing not fully implemented")
            
        elif command == "show" and len(parts) > 1:
            game_id = parts[1]
            # Implementation would show game state
            print("Game display not fully implemented")
            
        elif command == "move" and len(parts) > 3:
            game_id = parts[1]
            try:
                row = int(parts[2])
                col = int(parts[3])
                # Implementation would make move in game
                print("Game moves not fully implemented")
            except ValueError:
                print("Row and column must be numbers between 0 and 2")
        else:
            self.help_game()
    
    def do_verbose(self, arg):
        """
        Toggle verbose mode for debugging.
        Usage: verbose [on|off]
        """
        if arg.lower() in ("on", "true", "1"):
            self.verbose_mode = True
            print("Verbose mode enabled.")
        elif arg.lower() in ("off", "false", "0"):
            self.verbose_mode = False
            print("Verbose mode disabled.")
        else:
            self.verbose_mode = not self.verbose_mode
            print(f"Verbose mode {'enabled' if self.verbose_mode else 'disabled'}.")
            
        # Update logging level
        logging.getLogger('lsnp').setLevel(
            logging.DEBUG if self.verbose_mode else logging.INFO
        )
    
    def do_exit(self, arg):
        """Exit the LSNP application."""
        if self.running:
            self.stop_network()
            
        print("Exiting LSNP. Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the LSNP application."""
        return self.do_exit(arg)
    
    def default(self, line):
        """Handle unknown commands."""
        print(f"Unknown command: {line}")
        print("Type 'help' for a list of commands.")
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
        

def run_interface(username: Optional[str] = None):
    """Start the LSNP interface"""
    interface = LSNPInterface(username)
    
    try:
        interface.cmdloop()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting...")
        interface.stop_network()
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        interface.stop_network()
    

if __name__ == "__main__":
    # Get username from command line if provided
    username = sys.argv[1] if len(sys.argv) > 1 else None
    run_interface(username)