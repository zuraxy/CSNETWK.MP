#!/usr/bin/env python3
"""
Working Textual UI for P2P Chat
Complete implementation that actually works
"""
import sys
import os
import threading
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, Static, Header, Footer
from textual.screen import Screen
from textual.message import Message

# Try to import peer integration
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from peer.network.network_manager import NetworkManager
    from peer.discovery.peer_manager import PeerManager
    from peer.core.message_handler import MessageHandler
    PEER_AVAILABLE = True
    print("DEBUG: P2P modules imported successfully")
except Exception as e:
    print(f"DEBUG: P2P modules not available: {e}")
    PEER_AVAILABLE = False


class WorkingSetupScreen(Screen):
    """Working setup screen"""
    
    class SetupComplete(Message):
        def __init__(self, username: str, verbose_mode: bool = False):
            super().__init__()
            self.username = username
            self.verbose_mode = verbose_mode
    
    def __init__(self):
        super().__init__()
        self.verbose_mode = False
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("🌐 P2P Chat Setup", classes="title")
            yield Label("Enter your username to join the P2P network")
            yield Input(placeholder="Enter username", id="username-input")
            
            with Horizontal():
                yield Button("Enable Verbose Mode", id="verbose-toggle", variant="default")
                yield Static("OFF", id="verbose-status")
            
            with Horizontal():
                yield Button("Join Network", id="join-btn", variant="primary")
                yield Button("Quit", id="quit-btn", variant="error")
            
            yield Static("Ready to connect", id="status")
    
    def on_mount(self) -> None:
        self.query_one("#status", Static).update("✅ Enter username and click Join Network")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        print(f"DEBUG: Setup screen button pressed: {event.button.id}")
        
        if event.button.id == "verbose-toggle":
            self.verbose_mode = not self.verbose_mode
            status_text = "ON" if self.verbose_mode else "OFF"
            self.query_one("#verbose-status", Static).update(status_text)
            
            button_text = "Disable Verbose Mode" if self.verbose_mode else "Enable Verbose Mode"
            event.button.label = button_text
            
            self.query_one("#status", Static).update(f"Verbose mode: {status_text}")
            
        elif event.button.id == "join-btn":
            username_input = self.query_one("#username-input", Input)
            username = username_input.value.strip()
            
            print(f"DEBUG: Join button clicked with username: '{username}'")
            
            if not username:
                self.query_one("#status", Static).update("❌ Please enter a username!")
                return
            
            self.query_one("#status", Static).update(f"🔄 Connecting as {username}...")
            
            # Post message to parent app
            print(f"DEBUG: Posting SetupComplete message")
            self.post_message(self.SetupComplete(username, self.verbose_mode))
            
        elif event.button.id == "quit-btn":
            print("DEBUG: Quit button pressed")
            self.app.exit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        print(f"DEBUG: Input submitted: {event.value}")
        username = event.value.strip()
        if username:
            self.post_message(self.SetupComplete(username, self.verbose_mode))


class WorkingP2PChatApp(App):
    """Working P2P Chat application"""
    
    CSS = """
    .title {
        text-align: center;
        text-style: bold;
        color: blue;
        margin-bottom: 1;
    }
    
    .main-container {
        padding: 1;
    }
    
    .chat-area {
        border: solid blue;
        padding: 1;
        height: 20;
        margin-bottom: 1;
    }
    
    .peer-area {
        border: solid green;
        padding: 1;
        height: 8;
        margin-bottom: 1;
    }
    
    .command-area {
        border: solid yellow;
        padding: 1;
        height: 5;
        margin-bottom: 1;
    }
    
    .status-area {
        border: solid red;
        padding: 1;
        height: 3;
    }
    
    Button {
        margin-right: 1;
    }
    
    Input {
        margin-right: 1;
        width: 50;
    }
    
    .message {
        margin-bottom: 1;
    }
    """
    
    TITLE = "P2P Chat - Working Version"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        print("DEBUG: Initializing WorkingP2PChatApp")
        
        self.username = ""
        self.verbose_mode = False
        self.is_connected = False
        self.message_count = 0
        
        # Initialize P2P components if available
        global PEER_AVAILABLE
        if PEER_AVAILABLE:
            try:
                self.network_manager = NetworkManager()
                self.peer_manager = PeerManager()
                self.message_handler = MessageHandler(self.network_manager, self.peer_manager)
                self.peer_manager.set_network_manager(self.network_manager)
                print("DEBUG: P2P components initialized")
            except Exception as e:
                print(f"DEBUG: Error initializing P2P: {e}")
                PEER_AVAILABLE = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(classes="main-container"):
            # Chat area
            with Container(classes="chat-area"):
                yield Label("📬 Chat Messages", classes="title")
                yield Static("No messages yet", id="chat-content")
            
            # Peer list
            with Container(classes="peer-area"):
                yield Label("👥 Connected Peers", classes="title")
                yield Static("No peers connected", id="peer-list")
            
            # Command area
            with Container(classes="command-area"):
                yield Label("💬 Send Message", classes="title")
                with Horizontal():
                    yield Input(placeholder="Type your message...", id="message-input")
                    yield Button("POST", id="post-btn", variant="primary")
                    yield Button("DM", id="dm-btn", variant="default")
                    yield Button("PROFILE", id="profile-btn", variant="default")
            
            # Status area
            with Container(classes="status-area"):
                yield Static("Not connected", id="status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        print("DEBUG: App mounted, showing setup screen")
        self.push_screen(WorkingSetupScreen())
    
    def on_working_setup_screen_setup_complete(self, message: WorkingSetupScreen.SetupComplete) -> None:
        """Handle setup completion using Textual's automatic message routing"""
        print(f"DEBUG: Setup complete received! Username: {message.username}, Verbose: {message.verbose_mode}")
        
        self.username = message.username
        self.verbose_mode = message.verbose_mode
        
        print("DEBUG: Popping setup screen to return to main UI...")
        # First, pop the setup screen to return to main UI
        self.pop_screen()
        
        # Small delay to ensure screen transition completes
        time.sleep(0.1)
        
        print("DEBUG: Updating main UI to show connecting status...")
        # Update UI immediately to show we're connecting
        self.query_one("#status", Static).update(f"🔄 Connecting as {self.username}...")
        self.add_chat_message("SYSTEM", f"🔄 Connecting {self.username} to P2P network...")
        
        # Start P2P system in background to avoid blocking UI
        if PEER_AVAILABLE:
            # Use threading to start P2P system without blocking
            threading.Thread(target=self._start_p2p_system, daemon=True).start()
        else:
            # Demo mode
            self._setup_demo_mode()
    
    def _start_p2p_system(self):
        """Start P2P system without blocking UI"""
        try:
            print("DEBUG: Starting P2P system in background...")
            
            # Set up user ID
            network_info = self.network_manager.get_network_info()
            user_id = f"{self.username}@{network_info['local_ip']}"
            self.peer_manager.set_user_id(user_id)
            
            print(f"DEBUG: User ID set to: {user_id}")
            
            # Set verbose mode
            self.message_handler.set_verbose_mode(self.verbose_mode)
            print(f"DEBUG: Verbose mode set to: {self.verbose_mode}")
            
            # Start networking (these might be blocking)
            print("DEBUG: Starting network listener...")
            self.network_manager.start_listening()
            print("DEBUG: Network listener started")
            
            print("DEBUG: Starting peer discovery...")
            self.peer_manager.start_discovery()
            print("DEBUG: Peer discovery started")
            
            self.is_connected = True
            
            print("DEBUG: P2P system started, updating UI...")
            
            # Update UI from main thread - try immediate update first
            try:
                print("DEBUG: Attempting direct UI update...")
                self._update_connection_success(user_id, network_info)
                print("DEBUG: Direct UI update successful")
            except Exception as direct_error:
                print(f"DEBUG: Direct update failed: {direct_error}, trying call_from_thread...")
                # Fallback to call_from_thread
                self.call_from_thread(self._update_connection_success, user_id, network_info)
            
        except Exception as e:
            print(f"DEBUG: Error starting P2P: {e}")
            import traceback
            traceback.print_exc()
            try:
                self._update_connection_error(str(e))
            except:
                self.call_from_thread(self._update_connection_error, str(e))
    
    def _update_connection_success(self, user_id, network_info):
        """Update UI for successful connection"""
        print("DEBUG: Updating UI for successful connection...")
        
        # Update status
        self.query_one("#status", Static).update(
            f"✅ Connected as {user_id} | Verbose: {self.verbose_mode} | Port: {network_info['local_port']}"
        )
        
        # Add welcome messages
        self.add_chat_message("SYSTEM", f"🎉 Welcome {self.username}! You're now connected to the P2P network.")
        self.add_chat_message("SYSTEM", "💡 Type a message and click POST to broadcast to all peers.")
        self.add_chat_message("SYSTEM", f"🔧 Verbose mode: {'ON' if self.verbose_mode else 'OFF'}")
        
        print("DEBUG: UI updated successfully")
    
    def _update_connection_error(self, error_msg):
        """Update UI for connection error"""
        self.query_one("#status", Static).update(f"❌ Error: {error_msg}")
        self.add_chat_message("SYSTEM", f"❌ Failed to start P2P system: {error_msg}")
    
    def _setup_demo_mode(self):
        """Set up demo mode when P2P is not available"""
        self.query_one("#status", Static).update(f"🔧 Demo mode - {self.username} (Verbose: {self.verbose_mode})")
        self.add_chat_message("SYSTEM", f"🎭 Demo mode active for {self.username}")
        self.add_chat_message("SYSTEM", "ℹ️  P2P modules not available - UI functionality only")
    
    def add_chat_message(self, sender: str, content: str):
        """Add a message to the chat area"""
        self.message_count += 1
        timestamp = f"[{self.message_count:03d}]"
        
        if sender == "SYSTEM":
            message = f"{timestamp} 🔧 {content}"
        else:
            message = f"{timestamp} {sender}: {content}"
        
        # Get current content
        chat_content = self.query_one("#chat-content", Static)
        current = chat_content.renderable
        
        if current == "No messages yet":
            new_content = message
        else:
            new_content = f"{current}\n{message}"
        
        chat_content.update(new_content)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        print(f"DEBUG: Main app button pressed: {event.button.id}")
        
        if not self.is_connected and event.button.id != "quit-btn":
            self.add_chat_message("SYSTEM", "❌ Please connect first!")
            return
        
        if event.button.id == "post-btn":
            message_input = self.query_one("#message-input", Input)
            content = message_input.value.strip()
            
            if not content:
                self.add_chat_message("SYSTEM", "❌ Please enter a message to send!")
                return
            
            message_input.value = ""  # Clear input
            
            if PEER_AVAILABLE and self.is_connected:
                # Send actual P2P message
                try:
                    sent_count = self.message_handler.send_post_message(content)
                    self.add_chat_message(f"{self.username} (YOU)", content)
                    self.add_chat_message("SYSTEM", f"📡 Message broadcast to {sent_count} peers")
                except Exception as e:
                    self.add_chat_message("SYSTEM", f"❌ Send error: {e}")
            else:
                # Demo mode
                self.add_chat_message(f"{self.username} (DEMO)", content)
                self.add_chat_message("SYSTEM", "📡 Demo message sent (P2P not available)")
        
        elif event.button.id == "dm-btn":
            self.add_chat_message("SYSTEM", "💬 DM feature - Enter recipient as 'username@ip' in next message")
        
        elif event.button.id == "profile-btn":
            self.add_chat_message("SYSTEM", "👤 Profile feature - Share your profile with all peers")
            if PEER_AVAILABLE and self.is_connected:
                try:
                    sent_count = self.message_handler.send_profile_message(
                        display_name=self.username,
                        status="Active P2P user"
                    )
                    self.add_chat_message("SYSTEM", f"👤 Profile shared with {sent_count} peers")
                except Exception as e:
                    self.add_chat_message("SYSTEM", f"❌ Profile error: {e}")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in message input"""
        if event.input.id == "message-input":
            # Simulate clicking POST button
            content = event.value.strip()
            if content:
                event.input.value = ""  # Clear input
                # Manually trigger POST
                if PEER_AVAILABLE and self.is_connected:
                    try:
                        sent_count = self.message_handler.send_post_message(content)
                        self.add_chat_message(f"{self.username} (YOU)", content)
                        self.add_chat_message("SYSTEM", f"📡 Message broadcast to {sent_count} peers")
                    except Exception as e:
                        self.add_chat_message("SYSTEM", f"❌ Send error: {e}")
                else:
                    self.add_chat_message(f"{self.username} (DEMO)", content)
    
    def action_quit(self) -> None:
        """Quit the application"""
        if PEER_AVAILABLE and self.is_connected:
            try:
                self.peer_manager.stop_discovery()
                self.network_manager.stop_listening()
                print("DEBUG: P2P system stopped")
            except Exception as e:
                print(f"DEBUG: Error stopping P2P: {e}")
        
        self.exit()


def main():
    print("DEBUG: Starting working Textual UI...")
    app = WorkingP2PChatApp()
    try:
        app.run()
    except Exception as e:
        print(f"DEBUG: App error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
