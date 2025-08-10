#!/usr/bin/env python3
"""
Improved Textual UI for P2P Chat
A more intuitive and responsive interface with clear navigation
"""
import sys
import os
import threading
import time
import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Button, Label, Input  # Use Input instead of TextArea
from textual.widgets import Static, Header, Footer, Select, Tabs, Tab, Rule
from textual.screen import Screen, ModalScreen
from textual.message import Message
from textual import events

# Import P2P modules
try:
    from peer.network.network_manager import NetworkManager
    from peer.discovery.peer_manager import PeerManager
    from peer.core.message_handler import MessageHandler
    PEER_AVAILABLE = True
    print("DEBUG: P2P modules imported successfully")
except Exception as e:
    print(f"DEBUG: P2P modules not available: {e}")
    PEER_AVAILABLE = False


class ChatMessage(Static):
    """A styled chat message widget with timestamp, sender, and content"""
    
    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }
    
    ChatMessage.system {
        border-left: solid $success;
        color: $success;
    }
    
    ChatMessage.post {
        border-left: solid $primary;
    }
    
    ChatMessage.dm {
        border-left: solid $warning;
        color: $warning;
    }
    
    ChatMessage.error {
        border-left: solid $error;
        color: $error;
    }
    
    ChatMessage .meta {
        color: $text-muted;
        margin-right: 1;
    }
    
    ChatMessage .sender {
        text-style: bold;
        margin-right: 1;
    }
    
    ChatMessage .content {
        margin-top: 1;
    }
    """
    
    def __init__(
        self, 
        sender: str, 
        content: str, 
        message_type: str = "post",
        timestamp: str = None
    ):
        super().__init__()
        self.sender = sender
        self.content = content
        self.message_type = message_type.lower()
        self.timestamp = timestamp or datetime.datetime.now().strftime("%H:%M:%S")
    
    def compose(self) -> ComposeResult:
        # Add CSS class based on message type
        self.add_class(self.message_type)
        
        # Create components
        with Container():
            with Horizontal():
                yield Static(f"[{self.timestamp}]", classes="meta")
                yield Static(f"{self.sender}", classes="sender")
            yield Static(f"{self.content}", classes="content")


class SetupScreen(Screen):
    """Setup screen for username and options"""
    
    class SetupComplete(Message):
        def __init__(self, username: str, verbose_mode: bool = False):
            super().__init__()
            self.username = username
            self.verbose_mode = verbose_mode
    
    def __init__(self):
        super().__init__()
        self.verbose_mode = False
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(classes="setup-container"):
            yield Label("🌐 P2P Chat Setup", id="setup-title")
            yield Label("Enter your username to join the P2P network")
            yield Input(placeholder="Enter username", id="username-input")
            
            with Horizontal(classes="setup-buttons"):
                yield Button("Enable Verbose Mode", id="verbose-toggle", variant="default")
                yield Static("OFF", id="verbose-status")
            
            with Horizontal(classes="setup-buttons"):
                yield Button("Join Network", id="join-btn", variant="primary")
                yield Button("Quit", id="quit-btn", variant="error")
            
            yield Static("Ready to connect", id="status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        # Focus the username input immediately
        self.query_one("#username-input", Input).focus()
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
        with Container(id="dm-modal"):
            yield Label("💬 Send Direct Message", id="dm-title")
            
            # Get available peers
            peers = self.peer_manager.get_peer_list() if self.peer_manager else []
            if peers:
                peer_options = [(peer_id, peer_id) for peer_id in peers]
                yield Label("Select recipient:")
                yield Select(peer_options, id="recipient-select", prompt="Choose a peer...")
            else:
                yield Label("No peers available")
                yield Static("Discover peers first before sending DMs", id="no-peers")
            
            yield Label("Message:")
            yield Input(placeholder="Type your direct message...", id="dm-input")
            
            with Horizontal():
                yield Button("Send DM", id="send-dm-btn", variant="primary", disabled=len(peers) == 0)
                yield Button("Cancel", id="cancel-btn", variant="default")
    
    def on_mount(self) -> None:
        # Focus the input or select as appropriate
        if self.peer_manager and self.peer_manager.get_peer_list():
            self.query_one("#recipient-select", Select).focus()
        else:
            try:
                self.query_one("#cancel-btn", Button).focus()
            except:
                pass
    
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
            # Try to get recipient
            try:
                recipient_select = self.query_one("#recipient-select", Select)
                if recipient_select.value and event.value.strip():
                    # Trigger send button
                    send_btn = self.query_one("#send-dm-btn", Button)
                    if not send_btn.disabled:
                        send_btn.press()
            except:
                pass


class ProfileScreen(ModalScreen):
    """Modal screen for updating profile"""
    
    class ProfileUpdated(Message):
        def __init__(self, display_name: str, status: str):
            super().__init__()
            self.display_name = display_name
            self.status = status
    
    def compose(self) -> ComposeResult:
        with Container(id="profile-modal"):
            yield Label("👤 Update Profile", id="profile-title")
            
            yield Label("Display Name:")
            yield Input(placeholder="Your display name", id="display-name-input")
            
            yield Label("Status Message:")
            yield Input(placeholder="What's on your mind?", id="status-input")
            
            with Horizontal():
                yield Button("Update Profile", id="update-profile-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")
    
    def on_mount(self) -> None:
        # Set initial values if available from parent app
        app = self.app
        if hasattr(app, "username"):
            self.query_one("#display-name-input", Input).value = app.username
        
        # Focus the display name input
        self.query_one("#display-name-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "update-profile-btn":
            display_name = self.query_one("#display-name-input", Input).value.strip()
            status = self.query_one("#status-input", Input).value.strip()
            
            if not display_name:
                # Use app username if available
                app = self.app
                if hasattr(app, "username"):
                    display_name = app.username
                else:
                    display_name = "Anonymous"
            
            if not status:
                status = "Available"
            
            self.post_message(self.ProfileUpdated(display_name, status))
            self.dismiss()
            
        elif event.button.id == "cancel-btn":
            self.dismiss()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Move focus to next input or submit
        if event.input.id == "display-name-input":
            self.query_one("#status-input", Input).focus()
        elif event.input.id == "status-input":
            # Submit the form
            self.query_one("#update-profile-btn", Button).press()


class ImprovedP2PChatApp(App):
    """Improved P2P Chat application with intuitive navigation and better updates"""
    
    CSS = """
    /* Global Styles */
    Screen {
        background: $surface;
        color: $text;
    }
    
    /* Tab & Header Styles */
    #main-tabs {
        dock: top;
        height: 3;
        margin-bottom: 1;
        background: $panel;
    }
    
    #main-content {
        width: 100%;
        height: 100%;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    /* Chat Tab */
    #chat-content {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }
    
    #message-input-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    #message-input {
        width: 3fr;
        height: 3;
    }
    
    #post-btn {
        width: 1fr;
        height: 3;
        min-width: 10;
        margin-left: 1;
    }
    
    #input-help {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        color: $text-muted;
    }
    
    /* Peers Tab */
    #peers-container {
        width: 100%;
        height: 100%;
        margin: 0 1;
        padding: 1;
    }
    
    #peer-list {
        width: 100%;
        height: 1fr;
        border: solid $success;
        padding: 1;
        overflow-y: auto;
    }
    
    #peer-actions {
        width: 100%;
        height: auto;
        margin-top: 1;
        align-horizontal: center;
    }
    
    #peer-actions Button {
        margin: 0 1;
        min-width: 12;
    }
    
    /* Settings Tab */
    #settings-container {
        width: 100%;
        height: 100%;
        margin: 0 1;
        padding: 1;
    }
    
    #settings-list {
        width: 100%;
        height: 1fr;
        border: solid $warning;
        padding: 1;
    }
    
    /* Status Bar */
    #status-container {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
    }
    
    /* Modal Screens */
    DMScreen, ProfileScreen {
        align: center middle;
    }
    
    #dm-modal, #profile-modal {
        background: $surface;
        border: thick $primary;
        padding: 2;
        width: 60;
        height: auto;
        max-height: 20;
    }
    
    #dm-title, #profile-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    /* Setup Screen */
    #setup-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
    }
    
    .setup-container {
        align: center middle;
        width: 100%;
        height: 100%;
        padding: 2;
    }
    
    .setup-buttons {
        margin: 1;
        height: 3;
    }
    
    #status {
        text-align: center;
        margin-top: 2;
        height: 2;
    }
    
    #verbose-status {
        min-width: 3;
        max-width: 5;
        text-align: center;
        margin-left: 1;
    }
    """
    
    TITLE = "Improved P2P Chat"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("tab", "focus_next", "Next"),
        ("shift+tab", "focus_previous", "Previous"),
        ("enter", "send_message", "Send Message"),
        ("ctrl+d", "open_dm", "Direct Message"),
        ("ctrl+p", "open_profile", "Profile"),
        ("f1", "show_help", "Help"),
    ]
    
    def __init__(self):
        super().__init__()
        print("DEBUG: Initializing ImprovedP2PChatApp")
        
        self.username = ""
        self.verbose_mode = False
        self.is_connected = False
        self.message_count = 0
        self.active_tab = "chat"
        
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
        """Create app layout with tabbed interface"""
        yield Header()
        
        # Main tabs for navigation
        with Tabs(id="main-tabs"):
            yield Tab("📬 Chat", id="chat-tab")
            yield Tab("👥 Peers", id="peers-tab")
            yield Tab("⚙️ Settings", id="settings-tab")
        
        # Main content area
        with Container(id="main-content"):
            # Chat tab content
            with Container(id="chat-container"):
                yield Label("Chat Messages", classes="title")
                yield Container(id="chat-content")
                yield Static("Type your message and press Enter or POST button:", id="input-help")
                with Horizontal(id="message-input-container"):
                    yield Input(placeholder="Type your message here...", id="message-input")
                    yield Button("POST", id="post-btn", variant="primary")
            
            # Peers tab content (initially hidden)
            with Container(id="peers-container", classes="hidden"):
                yield Label("Connected Peers", classes="title")
                yield Static(id="peer-list")
                with Horizontal(id="peer-actions"):
                    yield Button("Send DM", id="open-dm-btn", variant="primary")
                    yield Button("Refresh", id="refresh-peers-btn", variant="default")
            
            # Settings tab content (initially hidden)
            with Container(id="settings-container", classes="hidden"):
                yield Label("Settings & Profile", classes="title")
                with Container(id="settings-list"):
                    yield Static("User: Not connected", id="user-info")
                    yield Rule()
                    yield Static("Verbose Mode: OFF", id="verbose-info")
                    yield Rule()
                    yield Static("Network: Not connected", id="network-info")
                    yield Rule()
                    yield Static("Profile Status: Not set", id="profile-info")
                with Horizontal(id="settings-actions"):
                    yield Button("Update Profile", id="open-profile-btn", variant="primary")
                    yield Button("Toggle Verbose", id="toggle-verbose-btn", variant="default")
        
        # Status bar at the bottom
        with Container(id="status-container"):
            yield Static("Not connected", id="status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """When app is mounted, show setup screen"""
        print("DEBUG: App mounted, showing setup screen")
        self.push_screen(SetupScreen())
    
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab switching"""
        tab_id = event.tab.id
        print(f"DEBUG: Tab activated: {tab_id}")
        
        # Hide all content containers
        self.query_one("#chat-container").add_class("hidden")
        self.query_one("#peers-container").add_class("hidden")
        self.query_one("#settings-container").add_class("hidden")
        
        # Show the selected container
        if tab_id == "chat-tab":
            self.query_one("#chat-container").remove_class("hidden")
            self.active_tab = "chat"
            self.query_one("#message-input", Input).focus()
        elif tab_id == "peers-tab":
            self.query_one("#peers-container").remove_class("hidden")
            self.active_tab = "peers"
            self._update_peer_list()
        elif tab_id == "settings-tab":
            self.query_one("#settings-container").remove_class("hidden")
            self.active_tab = "settings"
            self._update_settings_display()
    
    def on_setup_screen_setup_complete(self, message: SetupScreen.SetupComplete) -> None:
        """Handle setup completion from setup screen"""
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
        self.add_chat_message("SYSTEM", f"🔄 Connecting {self.username} to P2P network...", "system")
        
        # Start P2P system in background to avoid blocking UI
        if PEER_AVAILABLE:
            # Use threading to start P2P system without blocking
            threading.Thread(target=self._start_p2p_system, daemon=True).start()
        else:
            # Demo mode
            self._setup_demo_mode()
    
    def _start_p2p_system(self):
        """Start P2P system in a background thread"""
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
                self.call_from_thread(self.add_chat_message, "SYSTEM", f"🆕 New peer discovered: {peer_id}", "system")
            
            def on_peer_lost(peer_id):
                print(f"DEBUG: Peer lost: {peer_id}")
                self.call_from_thread(self._update_peer_list)
                self.call_from_thread(self.add_chat_message, "SYSTEM", f"📤 Peer disconnected: {peer_id}", "system")
            
            self.peer_manager.on_peer_discovered = on_peer_discovered
            self.peer_manager.on_peer_lost = on_peer_lost
            
            # Set up message handlers for incoming messages
            self._setup_message_handlers()
            
            # Set verbose mode
            self.message_handler.set_verbose_mode(self.verbose_mode)
            print(f"DEBUG: Verbose mode set to: {self.verbose_mode}")
            
            # Start networking components
            print("DEBUG: Starting network listener...")
            self.network_manager.start_listening()
            print("DEBUG: Network listener started")
            
            print("DEBUG: Starting peer discovery...")
            self.peer_manager.start_discovery()
            print("DEBUG: Peer discovery started")
            
            self.is_connected = True
            
            print("DEBUG: P2P system started, updating UI...")
            
            # Update UI from main thread
            self.call_from_thread(self._update_connection_success, user_id, network_info)
            
        except Exception as e:
            print(f"DEBUG: Error starting P2P: {e}")
            import traceback
            traceback.print_exc()
            self.call_from_thread(self._update_connection_error, str(e))
    
    def _update_connection_success(self, user_id, network_info):
        """Update UI after successful P2P connection"""
        print("DEBUG: Updating UI for successful connection...")
        
        # Update status bar
        self.query_one("#status", Static).update(
            f"✅ Connected as {user_id} | Verbose: {'ON' if self.verbose_mode else 'OFF'} | Port: {network_info['local_port']}"
        )
        
        # Add welcome messages
        self.add_chat_message("SYSTEM", f"🎉 Welcome {self.username}! You're now connected to the P2P network.", "system")
        self.add_chat_message("SYSTEM", "💡 Type a message and click POST to broadcast to all peers.", "system")
        self.add_chat_message("SYSTEM", f"🔧 Verbose mode: {'ON' if self.verbose_mode else 'OFF'}", "system")
        
        # Update settings information
        self._update_settings_display()
        
        # Update peer list
        self._update_peer_list()
        
        # Set focus to message input for better UX
        self.query_one("#message-input", Input).focus()
        
        print("DEBUG: UI updated successfully")
        
        # Start periodic updates
        self._start_periodic_updates()
    
    def _update_connection_error(self, error_msg):
        """Update UI after connection error"""
        self.query_one("#status", Static).update(f"❌ Error: {error_msg}")
        self.add_chat_message("SYSTEM", f"❌ Failed to start P2P system: {error_msg}", "error")
        
        # Update settings
        self._update_settings_display()
    
    def _setup_demo_mode(self):
        """Set up demo mode when P2P is not available"""
        self.query_one("#status", Static).update(f"🔧 Demo mode - {self.username} (Verbose: {self.verbose_mode})")
        self.add_chat_message("SYSTEM", f"🎭 Demo mode active for {self.username}", "system")
        self.add_chat_message("SYSTEM", "ℹ️  P2P modules not available - UI functionality only", "system")
        
        # Update settings information
        self._update_settings_display()
    
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
            
            self.call_from_thread(self.add_chat_message, f"{display_name}", content, "post")
        
        def ui_dm_handler(msg_dict, addr):
            # Call original handler first
            original_dm_handler(msg_dict, addr)
            
            # Add to UI if message is for us
            to_user = msg_dict.get('TO', '')
            from_user = msg_dict.get('FROM', 'Unknown')
            content = msg_dict.get('CONTENT', '')
            
            if to_user == self.peer_manager.user_id:
                display_name = self.peer_manager.get_display_name(from_user)
                self.call_from_thread(self.add_chat_message, f"[DM] {display_name}", content, "dm")
        
        def ui_profile_handler(msg_dict, addr):
            # Call original handler first
            original_profile_handler(msg_dict, addr)
            
            # Add to UI
            user_id = msg_dict.get('USER_ID', 'Unknown')
            display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
            status = msg_dict.get('STATUS', '')
            
            self.call_from_thread(self.add_chat_message, "SYSTEM", f"👤 {display_name} updated profile: {status}", "system")
            
            # Update peer list to show new display name
            self.call_from_thread(self._update_peer_list)
        
        # Replace handlers
        self.message_handler.handle_post_message = ui_post_handler
        self.message_handler.handle_dm_message = ui_dm_handler
        self.message_handler.handle_profile_message = ui_profile_handler
    
    def _start_periodic_updates(self):
        """Start periodic UI updates for peer list and settings"""
        def periodic_update():
            while self.is_connected:
                try:
                    time.sleep(5)  # Update every 5 seconds
                    if self.is_connected:
                        self.call_from_thread(self._update_peer_list)
                        self.call_from_thread(self._update_settings_display)
                except Exception as e:
                    print(f"DEBUG: Error in periodic update: {e}")
                    break
        
        update_thread = threading.Thread(target=periodic_update, daemon=True)
        update_thread.start()
    
    def _update_peer_list(self):
        """Update the peer list display"""
        if not self.is_connected:
            self.query_one("#peer-list", Static).update("Not connected to P2P network")
            return
            
        if PEER_AVAILABLE:
            try:
                peer_list = self.peer_manager.get_peer_list()
                if peer_list:
                    peer_display = f"Connected peers ({len(peer_list)}):\n"
                    for peer_id in peer_list:
                        display_name = self.peer_manager.get_display_name(peer_id)
                        peer_info = self.peer_manager.get_peer_info(peer_id)
                        status = peer_info.get('status', 'Unknown')
                        peer_display += f"👤 {display_name} ({peer_id})\n   Status: {status}\n"
                    self.query_one("#peer-list", Static).update(peer_display.strip())
                else:
                    self.query_one("#peer-list", Static).update("No peers connected yet.\nWait for peer discovery or check your network.")
            except Exception as e:
                print(f"DEBUG: Error updating peer list: {e}")
                self.query_one("#peer-list", Static).update(f"Error updating peer list: {e}")
        else:
            self.query_one("#peer-list", Static).update("P2P system not available")
    
    def _update_settings_display(self):
        """Update the settings display with current information"""
        # Update user info
        if self.is_connected:
            user_id = self.peer_manager.user_id if PEER_AVAILABLE else f"{self.username} (demo)"
            self.query_one("#user-info", Static).update(f"User: {user_id}")
        else:
            self.query_one("#user-info", Static).update(f"User: {self.username} (not connected)")
        
        # Update verbose mode
        self.query_one("#verbose-info", Static).update(f"Verbose Mode: {'ON' if self.verbose_mode else 'OFF'}")
        
        # Update network info
        if PEER_AVAILABLE and self.is_connected:
            try:
                network_info = self.network_manager.get_network_info()
                network_text = f"Network: {network_info['local_ip']}:{network_info['local_port']}"
                self.query_one("#network-info", Static).update(network_text)
            except:
                self.query_one("#network-info", Static).update("Network: Error retrieving info")
        else:
            self.query_one("#network-info", Static).update("Network: Not connected")
        
        # Update profile info
        if PEER_AVAILABLE and self.is_connected:
            try:
                user_id = self.peer_manager.user_id
                display_name = self.peer_manager.get_display_name(user_id) or self.username
                status = self.peer_manager.get_peer_info(user_id).get('status', 'Not set')
                profile_text = f"Profile: {display_name}\nStatus: {status}"
                self.query_one("#profile-info", Static).update(profile_text)
            except:
                self.query_one("#profile-info", Static).update("Profile: Not set")
        else:
            self.query_one("#profile-info", Static).update("Profile: Not available in demo mode")
    
    def add_chat_message(self, sender: str, content: str, message_type: str = "post"):
        """Add a message to the chat area using the ChatMessage widget"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Create and mount the message widget
        chat_content = self.query_one("#chat-content", Container)
        message = ChatMessage(sender, content, message_type, timestamp)
        chat_content.mount(message)
        
        # Scroll to the bottom of the chat
        chat_content.scroll_end(animate=False)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the main UI"""
        print(f"DEBUG: Main app button pressed: {event.button.id}")
        
        # Handle post button
        if event.button.id == "post-btn":
            self._handle_post_button()
            
        # Handle DM button
        elif event.button.id == "open-dm-btn":
            self._handle_dm_button()
            
        # Handle profile button
        elif event.button.id == "open-profile-btn":
            self._handle_profile_button()
            
        # Handle refresh peers button
        elif event.button.id == "refresh-peers-btn":
            self._update_peer_list()
            self.add_chat_message("SYSTEM", "🔄 Refreshing peer list...", "system")
            
        # Handle toggle verbose button
        elif event.button.id == "toggle-verbose-btn":
            self._handle_toggle_verbose()
    
    def _handle_post_button(self):
        """Handle the POST button press"""
        if not self.is_connected:
            self.add_chat_message("SYSTEM", "❌ Please connect first!", "error")
            return
            
        message_input = self.query_one("#message-input", Input)
        content = message_input.value.strip()
        
        if not content:
            self.add_chat_message("SYSTEM", "❌ Please enter a message to send!", "error")
            return
        
        message_input.value = ""  # Clear input
        self._send_post_message(content)
        
        # Refocus input for continuous typing
        message_input.focus()
    
    def _handle_dm_button(self):
        """Handle the DM button press"""
        if not self.is_connected:
            self.add_chat_message("SYSTEM", "❌ Please connect first!", "error")
            return
            
        if PEER_AVAILABLE:
            peer_list = self.peer_manager.get_peer_list()
            if peer_list:
                self.push_screen(DMScreen(self.peer_manager))
            else:
                self.add_chat_message("SYSTEM", "❌ No peers available. Wait for peer discovery first.", "error")
        else:
            self.add_chat_message("SYSTEM", "❌ P2P system not available for DM", "error")
    
    def _handle_profile_button(self):
        """Handle the profile button press"""
        if not self.is_connected:
            self.add_chat_message("SYSTEM", "❌ Please connect first!", "error")
            return
            
        self.push_screen(ProfileScreen())
    
    def _handle_toggle_verbose(self):
        """Handle toggle verbose mode button"""
        if not PEER_AVAILABLE:
            self.add_chat_message("SYSTEM", "❌ P2P system not available", "error")
            return
            
        self.verbose_mode = not self.verbose_mode
        if self.is_connected:
            self.message_handler.set_verbose_mode(self.verbose_mode)
            
        self.add_chat_message("SYSTEM", f"🔧 Verbose mode: {'ON' if self.verbose_mode else 'OFF'}", "system")
        self._update_settings_display()
        
        # Update status bar
        status = self.query_one("#status", Static)
        current_status = status.renderable
        if "Connected as" in current_status:
            # Keep the connection info, just update verbose
            new_status = current_status.replace(
                f"Verbose: {'OFF' if self.verbose_mode else 'ON'}", 
                f"Verbose: {'ON' if self.verbose_mode else 'OFF'}"
            )
            status.update(new_status)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submissions"""
        if event.input.id == "message-input":
            self._handle_post_button()
    
    def on_dm_screen_dm_sent(self, message: DMScreen.DMSent) -> None:
        """Handle DM sent from DM screen"""
        if PEER_AVAILABLE and self.is_connected:
            try:
                success = self.message_handler.send_dm_message(message.recipient, message.message)
                if success:
                    self.add_chat_message(f"[DM TO {message.recipient}]", message.message, "dm")
                    self.add_chat_message("SYSTEM", f"📨 DM sent to {message.recipient}", "system")
                else:
                    self.add_chat_message("SYSTEM", f"❌ Failed to send DM to {message.recipient}", "error")
            except Exception as e:
                self.add_chat_message("SYSTEM", f"❌ DM error: {e}", "error")
        else:
            self.add_chat_message("SYSTEM", "❌ P2P system not available", "error")
    
    def on_profile_screen_profile_updated(self, message: ProfileScreen.ProfileUpdated) -> None:
        """Handle profile update from profile screen"""
        if PEER_AVAILABLE and self.is_connected:
            try:
                sent_count = self.message_handler.send_profile_message(
                    display_name=message.display_name,
                    status=message.status
                )
                self.add_chat_message("SYSTEM", f"👤 Profile updated: {message.display_name} - {message.status}", "system")
                self.add_chat_message("SYSTEM", f"👤 Profile shared with {sent_count} peers", "system")
                
                # Update settings display
                self._update_settings_display()
            except Exception as e:
                self.add_chat_message("SYSTEM", f"❌ Profile error: {e}", "error")
        else:
            self.add_chat_message("SYSTEM", "❌ P2P system not available", "error")
    
    def action_send_message(self) -> None:
        """Send message using keybinding"""
        self._handle_post_button()
    
    def action_open_dm(self) -> None:
        """Open DM dialog using keybinding"""
        self._handle_dm_button()
    
    def action_open_profile(self) -> None:
        """Open profile dialog using keybinding"""
        self._handle_profile_button()
    
    def action_show_help(self) -> None:
        """Show help information"""
        self.add_chat_message("SYSTEM", "📚 Available Commands:", "system")
        self.add_chat_message("SYSTEM", "• POST - Send a message to all peers", "system")
        self.add_chat_message("SYSTEM", "• DM - Send a direct message to a specific peer", "system")
        self.add_chat_message("SYSTEM", "• PROFILE - Update your display name and status", "system")
        self.add_chat_message("SYSTEM", "• F1 - Show this help", "system")
        self.add_chat_message("SYSTEM", "• Ctrl+D - Open DM dialog", "system")
        self.add_chat_message("SYSTEM", "• Ctrl+P - Open Profile dialog", "system")
        self.add_chat_message("SYSTEM", "• Tab - Switch between tabs", "system")
    
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
    
    def _send_post_message(self, content: str) -> None:
        """Helper method to send POST messages"""
        if not self.is_connected:
            self.add_chat_message("SYSTEM", "❌ Please connect first!", "error")
            return
        
        if PEER_AVAILABLE and self.is_connected:
            try:
                sent_count = self.message_handler.send_post_message(content)
                self.add_chat_message(f"{self.username} (YOU)", content, "post")
                self.add_chat_message("SYSTEM", f"📡 Message broadcast to {sent_count} peers", "system")
            except Exception as e:
                self.add_chat_message("SYSTEM", f"❌ Send error: {e}", "error")
        else:
            self.add_chat_message(f"{self.username} (DEMO)", content, "post")
            self.add_chat_message("SYSTEM", "📡 Demo message sent (P2P not available)", "system")


def main():
    """Main function to start the improved Textual UI"""
    print("DEBUG: Starting improved Textual UI...")
    app = ImprovedP2PChatApp()
    try:
        app.run()
    except Exception as e:
        print(f"DEBUG: App error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
