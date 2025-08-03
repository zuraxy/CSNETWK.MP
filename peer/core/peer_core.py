#!/usr/bin/env python3
"""
Refactored UDP Peer Implementation
Modular P2P peer using separated concerns and clean architecture
"""
import sys
import os

# Add parent directory to path for protocol access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peer.network.network_manager import NetworkManager
from peer.discovery.peer_manager import PeerManager
from peer.core.message_handler import MessageHandler
from peer.ui.user_interface import UserInterface
from peer.config.settings import DEFAULT_VERBOSE_MODE


class UDPPeerModular:
    """
    Modular P2P peer implementation with separated concerns
    """
    
    def __init__(self):
        # Initialize core modules
        self.network_manager = NetworkManager()
        self.peer_manager = PeerManager()
        self.message_handler = MessageHandler(self.network_manager, self.peer_manager)
        self.user_interface = UserInterface(self.message_handler, self.peer_manager)
        
        # Connect peer manager with network manager
        self.peer_manager.set_network_manager(self.network_manager)
        
        # Set up event callbacks
        self.peer_manager.on_peer_discovered = self._on_peer_discovered
        self.peer_manager.on_peer_lost = self._on_peer_lost
        
        # Display initialization info
        network_info = self.network_manager.get_network_info()
        print(f"Peer initialized on {network_info['local_ip']}:{network_info['local_port']}")
    
    def start(self):
        """Start the peer with all its components"""
        try:
            # Get user information
            username = input("Username: ")
            network_info = self.network_manager.get_network_info()
            user_id = f"{username}@{network_info['local_ip']}"
            self.peer_manager.set_user_id(user_id)
            
            # Configure verbose mode
            verbose_input = input(f"Enable verbose mode? (y/n, default={'y' if DEFAULT_VERBOSE_MODE else 'n'}): ").strip().lower()
            if verbose_input == '':
                verbose_mode = DEFAULT_VERBOSE_MODE
            else:
                verbose_mode = verbose_input != 'n'
            self.message_handler.set_verbose_mode(verbose_mode)
            
            print(f"Verbose mode: {'ON' if verbose_mode else 'OFF'}")
            print(f"Peer started as {user_id}")
            print(f"Listening on {network_info['local_ip']}:{network_info['local_port']}")
            
            # Start network listening
            self.network_manager.start_listening()
            
            # Start peer discovery
            self.peer_manager.start_discovery()
            
            # Start user interface
            self.user_interface.start_command_loop()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error starting peer: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components"""
        print("Shutting down peer...")
        
        # Stop UI
        self.user_interface.stop()
        
        # Stop discovery
        self.peer_manager.stop_discovery()
        
        # Stop network
        self.network_manager.stop_listening()
        
        print("Peer shutdown complete")
    
    def _on_peer_discovered(self, user_id):
        """Callback when a new peer is discovered"""
        if self.message_handler.verbose_mode:
            print(f"[PEER JOINED] {user_id}")
    
    def _on_peer_lost(self, user_id):
        """Callback when a peer is lost/timed out"""
        if self.message_handler.verbose_mode:
            print(f"[PEER LEFT] {user_id} (timeout)")
    
    def get_status(self):
        """Get current peer status information"""
        network_info = self.network_manager.get_network_info()
        peers = self.peer_manager.get_all_peers()
        
        return {
            'user_id': self.peer_manager.user_id,
            'network_info': network_info,
            'peer_count': len(peers),
            'peers': list(peers.keys()),
            'verbose_mode': self.message_handler.verbose_mode
        }


def main():
    """Main function to start the modular peer"""
    peer = UDPPeerModular()
    try:
        peer.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        peer.shutdown()


if __name__ == "__main__":
    main()
