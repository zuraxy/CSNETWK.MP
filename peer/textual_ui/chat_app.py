#!/usr/bin/env python3
"""
P2P Chat Textual Application
Modern TUI interface for the P2P chat system using Textual
"""
import sys
import os
import asyncio
from typing import Dict, Any
import base64
import mimetypes

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.reactive import reactive
from textual.screen import Screen
from textual.message import Message

from .components import (
    ChatMessageArea, PeerListWidget, CommandInput, StatusBar,
    ProfileDialog, DMDialog
)
from .peer_integration import TextualPeerInterface


class SetupScreen(Screen):
    """Initial setup screen for username and settings"""
    
    class SetupComplete(Message):
        """Message sent when setup is complete"""
        def __init__(self, username: str, verbose_mode: bool):
            super().__init__()
            self.username = username
            self.verbose_mode = verbose_mode
    
    def compose(self) -> ComposeResult:
        """Create the setup screen layout"""
        with Container(classes="setup-container"):
            yield Label("P2P Chat Setup", classes="setup-title")
            yield Label("Enter your username to join the P2P network", classes="setup-subtitle")
            yield Input(placeholder="Enter username", id="username-input", classes="setup-input")
            with Horizontal(classes="setup-options"):
                yield Button("Enable Verbose Mode", id="verbose-toggle", variant="default")
                yield Static("OFF", id="verbose-status", classes="verbose-indicator")
            with Horizontal(classes="setup-buttons"):
                yield Button("Join Network", id="join-btn", variant="primary")
                yield Button("Quit", id="quit-btn", variant="error")
    
    def __init__(self):
        super().__init__()
        self.verbose_mode = False
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses on setup screen"""
        print(f"DEBUG: SetupScreen button pressed: {event.button.id}")
        
        if event.button.id == "verbose-toggle":
            self.verbose_mode = not self.verbose_mode
            status_text = "ON" if self.verbose_mode else "OFF"
            self.query_one("#verbose-status", Static).update(status_text)
            
            # Update button text
            button_text = "Disable Verbose Mode" if self.verbose_mode else "Enable Verbose Mode"
            event.button.label = button_text
            
        elif event.button.id == "join-btn":
            username_input = self.query_one("#username-input", Input)
            username = username_input.value.strip()
            print(f"DEBUG: Join button - username: '{username}'")
            
            if not username:
                username_input.placeholder = "Username is required!"
                return
            
            print(f"DEBUG: Posting SetupComplete message with username: {username}")
            self.post_message(self.SetupComplete(username, self.verbose_mode))
            
        elif event.button.id == "quit-btn":
            print("DEBUG: Quit button pressed")
            self.app.exit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in username input"""
        if event.input.id == "username-input":
            username = event.value.strip()
            if username:
                self.post_message(self.SetupComplete(username, self.verbose_mode))


class P2PChatApp(App):
    """Main P2P Chat Textual Application"""
    
    # CSS_PATH = os.path.join(os.path.dirname(__file__), "styles.tcss")  # Temporarily disabled for stability
    
    TITLE = "P2P Chat - Textual UI"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("f1", "toggle_verbose", "Toggle Verbose"),
        ("f2", "show_peers", "Show Peers"),
    ]
    
    def __init__(self):
        print("DEBUG: Initializing P2PChatApp...")
        super().__init__()
        try:
            self.peer_interface = TextualPeerInterface()
            self.setup_callbacks()
            print("DEBUG: P2PChatApp initialization complete")
        except Exception as e:
            print(f"DEBUG: Error during app init: {e}")
            import traceback
            traceback.print_exc()
        
        # UI state
        self.username = ""
        self.is_connected = False
    
    def compose(self) -> ComposeResult:
        """Create the main application layout"""
        yield Header()
        
        with Grid(classes="main-grid"):
            # Chat message area
            self.chat_area = ChatMessageArea(classes="chat-area")
            yield self.chat_area
            
            # Peer list
            self.peer_list = PeerListWidget(classes="peer-list")
            yield self.peer_list
            
            # Command input area
            self.command_input = CommandInput(classes="command-area")
            yield self.command_input
            
            # Status bar
            self.status_bar = StatusBar(classes="status-bar")
            yield self.status_bar
        
        # Dialogs (hidden by default)
        self.profile_dialog = ProfileDialog(classes="profile-dialog")
        yield self.profile_dialog
        
        self.dm_dialog = DMDialog(classes="dm-dialog")
        yield self.dm_dialog
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted"""
        print("DEBUG: App on_mount called, showing setup screen...")
        # Show setup screen initially
        try:
            self.push_screen(SetupScreen())
            print("DEBUG: SetupScreen pushed successfully")
        except Exception as e:
            print(f"DEBUG: Error pushing setup screen: {e}")
            import traceback
            traceback.print_exc()
    
    def on_setup_screen_setup_complete(self, message: SetupScreen.SetupComplete) -> None:
        """Handle setup completion message"""
        print(f"DEBUG: Received setup complete message - username: {message.username}, verbose: {message.verbose_mode}")
        
        self.username = message.username
        verbose_mode = message.verbose_mode
        
        # Start the peer system
        print("DEBUG: Attempting to start peer system...")
        try:
            success = self.peer_interface.start_peer(self.username, verbose_mode)
            print(f"DEBUG: Peer start result: {success}")
            
            if success:
                self.is_connected = True
                print("DEBUG: Connection successful! Updating UI...")
                
                # Simple update: just change the title for now
                self.title = f"P2P Chat - {self.username}"
                print("DEBUG: Title updated successfully!")
                
            else:
                print("DEBUG: Peer start failed")
                self.title = f"P2P Chat - Connection Failed"
                
        except Exception as e:
            print(f"DEBUG: Exception during peer start: {e}")
            import traceback
            traceback.print_exc()
            self.title = f"P2P Chat - Error: {str(e)[:20]}"
    
    def setup_callbacks(self):
        """Set up callbacks for peer interface"""
        self.peer_interface.set_ui_callbacks(
            on_message_received=self.on_message_received,
            on_peer_discovered=self.on_peer_discovered,
            on_peer_lost=self.on_peer_lost,
            on_status_update=self.on_status_update
        )
    
    def on_message_received(self, message_type: str, sender: str, content: str):
        """Handle incoming messages from peer interface"""
        self.call_from_thread(self.chat_area.add_message, message_type, sender, content)
    
    def on_peer_discovered(self, user_id: str, display_name: str):
        """Handle peer discovered event"""
        # Update peer list
        peers = self.peer_interface.get_all_peers()
        self.call_from_thread(self.peer_list.update_peers, peers)
    
    def on_peer_lost(self, user_id: str, display_name: str):
        """Handle peer lost event"""
        # Update peer list
        peers = self.peer_interface.get_all_peers()
        self.call_from_thread(self.peer_list.update_peers, peers)
    
    def on_status_update(self, status: Dict[str, Any]):
        """Handle status updates from peer interface"""
        self.call_from_thread(
            self.status_bar.update_status,
            user_id=status.get('user_id'),
            peer_count=status.get('peer_count'),
            verbose_mode=status.get('verbose_mode'),
            local_address=status.get('local_address')
        )
    
    def on_command_input_command_submitted(self, event: CommandInput.CommandSubmitted) -> None:
        """Handle commands from the command input widget"""
        command = event.command
        args = event.args
        
        if command == "POST":
            if args:
                sent_count = self.peer_interface.send_post_message(args)
                if sent_count == 0:
                    self.chat_area.add_message("SYSTEM", "WARNING", 
                                             "No peers to send message to")
            else:
                self.chat_area.add_message("SYSTEM", "ERROR", 
                                         "Please enter a message to broadcast")
        
        elif command == "DM":
            # Show DM dialog
            peers = self.peer_interface.get_all_peers()
            if not peers:
                self.chat_area.add_message("SYSTEM", "ERROR", 
                                         "No peers available for direct messaging")
                return
            
            self.dm_dialog.update_available_peers(peers)
            self.dm_dialog.show_dialog()
        
        elif command == "PROFILE":
            # Show profile dialog
            self.profile_dialog.show_dialog()
        
        elif command == "LIST":
            peers = self.peer_interface.get_all_peers()
            if not peers:
                self.chat_area.add_message("SYSTEM", "INFO", "No peers connected")
            else:
                peer_list = []
                for user_id, info in peers.items():
                    display_name = info.get('display_name', user_id)
                    avatar_indicator = " 🖼️" if info.get('avatar', False) else ""
                    peer_list.append(f"• {display_name}{avatar_indicator}")
                
                peer_text = "\n".join(peer_list)
                self.chat_area.add_message("SYSTEM", "INFO", 
                                         f"Connected peers ({len(peers)}):\n{peer_text}")
        
        elif command == "VERBOSE":
            new_verbose = self.peer_interface.toggle_verbose_mode()
            # Status update will be handled by the peer interface callback
        
        elif command == "QUIT":
            self.action_quit()
        
        elif command == "ERROR":
            self.chat_area.add_message("SYSTEM", "ERROR", args)
    
    def on_profile_dialog_profile_submitted(self, event: ProfileDialog.ProfileSubmitted) -> None:
        """Handle profile submission"""
        display_name = event.display_name or self.username
        status = event.status or "Hello from P2P Chat!"
        avatar_path = event.avatar_path
        
        avatar_data = None
        avatar_type = None
        
        # Handle avatar file if provided
        if avatar_path and os.path.exists(avatar_path):
            try:
                file_size = os.path.getsize(avatar_path)
                if file_size > 20480:  # 20KB limit
                    self.chat_area.add_message("SYSTEM", "WARNING", 
                                             f"Avatar file is {file_size} bytes. Recommended max: 20KB")
                
                with open(avatar_path, 'rb') as f:
                    avatar_bytes = f.read()
                
                avatar_data = base64.b64encode(avatar_bytes).decode('utf-8')
                avatar_type = mimetypes.guess_type(avatar_path)[0] or 'application/octet-stream'
                
            except Exception as e:
                self.chat_area.add_message("SYSTEM", "ERROR", 
                                         f"Error reading avatar file: {e}")
        
        # Send profile update
        sent_count = self.peer_interface.send_profile_message(
            display_name, status, avatar_data, avatar_type
        )
        
        self.profile_dialog.hide_dialog()
    
    def on_profile_dialog_dialog_closed(self, event: ProfileDialog.DialogClosed) -> None:
        """Handle profile dialog closed"""
        self.profile_dialog.hide_dialog()
    
    def on_dm_dialog_dm_submitted(self, event: DMDialog.DMSubmitted) -> None:
        """Handle DM submission"""
        success = self.peer_interface.send_dm_message(event.recipient, event.message)
        
        if success:
            # Show the sent message in our chat
            self.chat_area.add_message("DM_SENT", f"To {event.recipient}", event.message)
        
        self.dm_dialog.hide_dialog()
    
    def on_dm_dialog_dialog_closed(self, event: DMDialog.DialogClosed) -> None:
        """Handle DM dialog closed"""
        self.dm_dialog.hide_dialog()
    
    def action_toggle_verbose(self) -> None:
        """Toggle verbose mode (F1 key)"""
        if self.is_connected:
            self.peer_interface.toggle_verbose_mode()
    
    def action_show_peers(self) -> None:
        """Show peers list (F2 key)"""
        if self.is_connected:
            peers = self.peer_interface.get_all_peers()
            self.peer_list.update_peers(peers)
    
    def action_quit(self) -> None:
        """Quit the application"""
        if self.is_connected:
            self.peer_interface.stop_peer()
        self.exit()


def main():
    """Main function to run the Textual P2P Chat app"""
    print("DEBUG: Starting main() function...")
    try:
        app = P2PChatApp()
        print("DEBUG: App created, running...")
        app.run()
        print("DEBUG: App finished normally")
    except Exception as e:
        print(f"DEBUG: Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
