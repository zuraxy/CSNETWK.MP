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
from textual.widgets import Button, Label, Input, Static, Header, Footer, Select
from textual.screen import Screen, ModalScreen
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
        with Container(classes="setup-container"):
            yield Label("🌐 P2P Chat Setup", classes="title")
            yield Label("Enter your username to join the P2P network")
            yield Input(placeholder="Enter username", id="username-input")
            
            with Horizontal(classes="setup-buttons"):
                yield Button("Enable Verbose Mode", id="verbose-toggle", variant="default")
                yield Static("OFF", id="verbose-status")
            
            with Horizontal(classes="setup-buttons"):
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


class DMScreen(ModalScreen):
    """Modal screen for sending direct messages"""
    
    class DMSent(Message):
        def __init__(self, recipient: str, message: str):
            super().__init__()
            self.recipient = recipient
            self.message = message
    
    def __init__(self, peer_manager):
        super().__init__()
        self.peer_manager = peer_manager
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("💬 Send Direct Message", classes="title")
            
            # Get available peers
            peers = self.peer_manager.get_peer_list() if self.peer_manager else []
            if peers:
                peer_options = [(peer_id, peer_id) for peer_id in peers]
                yield Label("Select recipient:")
                yield Select(peer_options, id="recipient-select")
            else:
                yield Label("No peers available")
                yield Static("Discover peers first before sending DMs", id="no-peers")
            
            yield Label("Message:")
            yield Input(placeholder="Type your direct message...", id="dm-input")
            
            with Horizontal():
                yield Button("Send DM", id="send-dm-btn", variant="primary", disabled=len(peers) == 0)
                yield Button("Cancel", id="cancel-btn", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-dm-btn":
            try:
                recipient_select = self.query_one("#recipient-select", Select)
                dm_input = self.query_one("#dm-input", Input)
                
                recipient = str(recipient_select.value) if recipient_select.value else ""
                message = dm_input.value.strip()
                
                if not recipient:
                    return
                
                if not message:
                    return
                
                # Send the DM message to parent
                self.post_message(self.DMSent(recipient, message))
                self.dismiss()
                
            except Exception as e:
                print(f"DEBUG: Error in DM screen: {e}")
                
        elif event.button.id == "cancel-btn":
            self.dismiss()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "dm-input":
            # Trigger send button
            try:
                send_btn = self.query_one("#send-dm-btn", Button)
                if not send_btn.disabled:
                    send_btn.press()
            except:
                pass


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
        height: 12;
        margin-bottom: 1;
    }
    
    .peer-area {
        border: solid green;
        padding: 1;
        height: 5;
        margin-bottom: 1;
    }
    
    .command-area {
        border: solid yellow;
        padding: 1;
        height: 6;
        margin-bottom: 1;
    }
    
    .status-area {
        border: solid red;
        padding: 1;
        height: 3;
    }
    
    Button {
        margin-right: 1;
        min-width: 8;
        max-width: 12;
        height: 3;
    }
    
    Input {
        height: 3;
    }
    
    #message-input {
        width: 1fr;
        margin-right: 1;
        min-width: 20;
        max-width: 60;
        height: 3;
    }
    
    #username-input {
        height: 3;
        width: 40;
        max-width: 60;
    }
    
    DMScreen {
        align: center middle;
    }
    
    DMScreen > Container {
        background: $surface;
        border: thick $primary;
        padding: 2;
        width: 60;
        height: auto;
    }
    
    Select {
        margin-bottom: 1;
        width: 100%;
        height: 3;
    }
    
    #dm-input {
        width: 100%;
        margin-bottom: 1;
        height: 3;
    }
    
    #input-help {
        color: $text-muted;
        margin-bottom: 1;
        text-align: center;
        height: 1;
    }
    
    /* Setup Screen Styles */
    .setup-container {
        align: center middle;
        padding: 2;
        max-width: 60;
        max-height: 20;
    }
    
    .setup-buttons {
        margin: 1;
        height: 3;
    }
    
    #status {
        text-align: center;
        margin-top: 1;
        height: 2;
    }
    
    #verbose-status {
        min-width: 3;
        max-width: 5;
        text-align: center;
    }
    """
    
    TITLE = "P2P Chat - Enhanced with Input Controls"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("tab", "focus_next", "Next"),
        ("shift+tab", "focus_previous", "Previous"),
        ("enter", "send_message", "Send Message"),
        ("ctrl+d", "open_dm", "Direct Message"),
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
            
            # Command area (always visible and accessible)
            with Container(classes="command-area"):
                yield Label("💬 Send Message", classes="title")
                yield Static("Type message and press Enter, or use buttons below:", id="input-help")
                with Horizontal():
                    yield Input(placeholder="Type your message here...", id="message-input")
                    yield Button("POST", id="post-btn", variant="primary")
                with Horizontal():
                    yield Button("DM", id="dm-btn", variant="default")
                    yield Button("PROFILE", id="profile-btn", variant="default")
                    yield Button("GAME", id="game-btn", variant="default")
                    yield Button("QUIT", id="quit-main-btn", variant="error")
            
            # Status area
            with Container(classes="status-area"):
                yield Label("🔧 System Status", classes="title")
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
            
            # Set up peer discovery callbacks for real-time updates
            def on_peer_discovered(peer_id):
                print(f"DEBUG: New peer discovered: {peer_id}")
                self.call_from_thread(self._update_peer_list)
                self.call_from_thread(self.add_chat_message, "SYSTEM", f"🆕 New peer discovered: {peer_id}")
            
            def on_peer_lost(peer_id):
                print(f"DEBUG: Peer lost: {peer_id}")
                self.call_from_thread(self._update_peer_list)
                self.call_from_thread(self.add_chat_message, "SYSTEM", f"📤 Peer disconnected: {peer_id}")
            
            self.peer_manager.on_peer_discovered = on_peer_discovered
            self.peer_manager.on_peer_lost = on_peer_lost
            
            # Set up message handlers for incoming messages
            self._setup_message_handlers()
            
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
            
            # Start periodic peer list updates
            self._start_periodic_updates()
            
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
        
        # Start periodic updates
        self._start_periodic_updates()
        
        # Set focus to message input for better UX
        try:
            message_input = self.query_one("#message-input", Input)
            message_input.focus()
        except Exception as e:
            print(f"DEBUG: Could not focus message input: {e}")
        
        print("DEBUG: UI updated successfully")
    
    def _setup_message_handlers(self):
        """Set up handlers for incoming P2P messages"""
        if not PEER_AVAILABLE or not self.is_connected:
            return
        
        # Store original message handlers
        original_post_handler = self.message_handler.handle_post_message
        original_dm_handler = self.message_handler.handle_dm_message
        original_profile_handler = self.message_handler.handle_profile_message
        
        def ui_post_handler(msg_dict, addr):
            # Call original handler first
            original_post_handler(msg_dict, addr)
            
            # Add to UI
            user_id = msg_dict.get('USER_ID', 'Unknown')
            content = msg_dict.get('CONTENT', '')
            display_name = self.peer_manager.get_display_name(user_id)
            
            self.call_from_thread(self.add_chat_message, f"{display_name}", content)
        
        def ui_dm_handler(msg_dict, addr):
            # Call original handler first
            original_dm_handler(msg_dict, addr)
            
            # Add to UI if message is for us
            to_user = msg_dict.get('TO', '')
            from_user = msg_dict.get('FROM', 'Unknown')
            content = msg_dict.get('CONTENT', '')
            
            if to_user == self.peer_manager.user_id:
                display_name = self.peer_manager.get_display_name(from_user)
                self.call_from_thread(self.add_chat_message, f"[DM] {display_name}", content)
        
        def ui_profile_handler(msg_dict, addr):
            # Call original handler first
            original_profile_handler(msg_dict, addr)
            
            # Add to UI
            user_id = msg_dict.get('USER_ID', 'Unknown')
            display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
            status = msg_dict.get('STATUS', '')
            
            self.call_from_thread(self.add_chat_message, "SYSTEM", f"👤 {display_name} updated profile: {status}")
        
        # Replace handlers
        self.message_handler.handle_post_message = ui_post_handler
        self.message_handler.handle_dm_message = ui_dm_handler
        self.message_handler.handle_profile_message = ui_profile_handler
    
    def _start_periodic_updates(self):
        """Start periodic UI updates"""
        def periodic_update():
            while self.is_connected:
                try:
                    time.sleep(10)  # Update every 10 seconds
                    if self.is_connected:
                        self.call_from_thread(self._update_peer_list)
                except Exception as e:
                    print(f"DEBUG: Error in periodic update: {e}")
                    break
        
        update_thread = threading.Thread(target=periodic_update, daemon=True)
        update_thread.start()
    
    def _update_peer_list(self):
        """Update the peer list display"""
        if PEER_AVAILABLE and self.is_connected:
            try:
                peer_list = self.peer_manager.get_peer_list()
                if peer_list:
                    peer_display = f"Connected peers ({len(peer_list)}):\n"
                    for peer_id in peer_list:
                        peer_info = self.peer_manager.get_peer_info(peer_id)
                        peer_display += f"  • {peer_id} ({peer_info['ip']}:{peer_info['port']})\n"
                    self.query_one("#peer-list", Static).update(peer_display.strip())
                else:
                    self.query_one("#peer-list", Static).update("No peers connected")
            except Exception as e:
                print(f"DEBUG: Error updating peer list: {e}")
                self.query_one("#peer-list", Static).update(f"Error updating peer list: {e}")
        else:
            self.query_one("#peer-list", Static).update("P2P system not available")
    
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
        
        if event.button.id == "quit-main-btn":
            self.action_quit()
            return
        
        if not self.is_connected and event.button.id not in ["quit-btn", "quit-main-btn"]:
            self.add_chat_message("SYSTEM", "❌ Please connect first!")
            return
        
        if event.button.id == "post-btn":
            message_input = self.query_one("#message-input", Input)
            content = message_input.value.strip()
            
            if not content:
                self.add_chat_message("SYSTEM", "❌ Please enter a message to send!")
                return
            
            message_input.value = ""  # Clear input
            self._send_post_message(content)
            # Refocus input for continuous typing
            message_input.focus()
        
        elif event.button.id == "dm-btn":
            # Show DM screen
            if PEER_AVAILABLE and self.is_connected:
                peer_list = self.peer_manager.get_peer_list()
                if peer_list:
                    self.push_screen(DMScreen(self.peer_manager))
                else:
                    self.add_chat_message("SYSTEM", "❌ No peers available. Wait for peer discovery first.")
            else:
                self.add_chat_message("SYSTEM", "❌ P2P system not available for DM")
        
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
    
    def on_dm_screen_dm_sent(self, message: DMScreen.DMSent) -> None:
        """Handle DM sent from DM screen"""
        if PEER_AVAILABLE and self.is_connected:
            try:
                success = self.message_handler.send_dm_message(message.recipient, message.message)
                if success:
                    self.add_chat_message(f"[DM TO {message.recipient}] {self.username}", message.message)
                    self.add_chat_message("SYSTEM", f"📨 DM sent to {message.recipient}")
                else:
                    self.add_chat_message("SYSTEM", f"❌ Failed to send DM to {message.recipient}")
            except Exception as e:
                self.add_chat_message("SYSTEM", f"❌ DM error: {e}")
        else:
            self.add_chat_message("SYSTEM", "❌ P2P system not available")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in message input"""
        if event.input.id == "message-input":
            content = event.value.strip()
            if content:
                event.input.value = ""  # Clear input
                self._send_post_message(content)
                # Refocus the input for continuous typing
                event.input.focus()
    
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
    
    def action_send_message(self) -> None:
        """Send message using Enter key"""
        try:
            message_input = self.query_one("#message-input", Input)
            if message_input.value.strip():
                # Trigger POST button
                self._send_post_message(message_input.value.strip())
                message_input.value = ""
        except Exception as e:
            print(f"DEBUG: Error in send_message action: {e}")
    
    def action_open_dm(self) -> None:
        """Open DM dialog using Ctrl+D"""
        try:
            if PEER_AVAILABLE and self.is_connected:
                peer_list = self.peer_manager.get_peer_list()
                if peer_list:
                    self.push_screen(DMScreen(self.peer_manager))
                else:
                    self.add_chat_message("SYSTEM", "❌ No peers available for DM")
            else:
                self.add_chat_message("SYSTEM", "❌ P2P system not available")
        except Exception as e:
            print(f"DEBUG: Error in open_dm action: {e}")
    
    def _send_post_message(self, content: str) -> None:
        """Helper method to send POST messages"""
        if not self.is_connected:
            self.add_chat_message("SYSTEM", "❌ Please connect first!")
            return
        
        if PEER_AVAILABLE and self.is_connected:
            try:
                sent_count = self.message_handler.send_post_message(content)
                self.add_chat_message(f"{self.username} (YOU)", content)
                self.add_chat_message("SYSTEM", f"📡 Message broadcast to {sent_count} peers")
            except Exception as e:
                self.add_chat_message("SYSTEM", f"❌ Send error: {e}")
        else:
            self.add_chat_message(f"{self.username} (DEMO)", content)
            self.add_chat_message("SYSTEM", "📡 Demo message sent (P2P not available)")


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
