#!/usr/bin/env python3
"""
Textual UI Components
Reusable widgets for the P2P Chat TUI application
"""
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

from textual.widgets import Static, Input, Button, Label, DataTable
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.console import Console
from rich.panel import Panel


class ChatMessageArea(VerticalScroll):
    """Scrollable area for displaying chat messages"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.console = Console(width=80)
    
    def add_message(self, message_type: str, sender: str, content: str, timestamp: Optional[str] = None):
        """Add a new message to the chat area"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create message display based on type
        if message_type == "POST":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [yellow]{sender}[/yellow]: {content}"
        elif message_type == "DM":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [magenta]DM from {sender}[/magenta]: {content}"
        elif message_type == "SYSTEM":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [green]SYSTEM[/green]: {content}"
        elif message_type == "PEER_JOIN":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [bright_green]→ {sender} joined[/bright_green]"
        elif message_type == "PEER_LEAVE":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [red]← {sender} left[/red]"
        elif message_type == "PROFILE":
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] [blue]👤 {sender} updated profile[/blue]: {content}"
        else:
            formatted_msg = f"[bold cyan][{timestamp}][/bold cyan] {sender}: {content}"
        
        # Add message to our list
        self.messages.append({
            'type': message_type,
            'sender': sender,
            'content': content,
            'timestamp': timestamp,
            'formatted': formatted_msg
        })
        
        # Create and add the message widget with type-specific class
        css_classes = f"message message-{message_type.lower()}"
        message_widget = Static(formatted_msg, classes=css_classes)
        self.mount(message_widget)
        
        # Auto-scroll to bottom
        self.scroll_end(animate=False)
    
    def clear_messages(self):
        """Clear all messages from the chat area"""
        self.messages.clear()
        for child in self.children:
            child.remove()


class PeerListWidget(Container):
    """Widget displaying list of connected peers"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.peers: Dict[str, Dict] = {}
    
    def compose(self):
        """Create the peer list layout"""
        with Vertical():
            yield Label("Connected Peers", classes="section-title")
            yield Static("No peers connected", id="peer-list", classes="peer-list")
    
    def update_peers(self, peers: Dict[str, Dict]):
        """Update the peer list display"""
        self.peers = peers
        
        if not peers:
            peer_display = "No peers connected"
        else:
            peer_lines = []
            for user_id, info in peers.items():
                # Extract display name if available
                display_name = info.get('display_name', user_id)
                avatar_info = " 🖼️" if info.get('avatar', False) else ""
                peer_lines.append(f"• {display_name}{avatar_info}")
            
            peer_display = "\n".join(peer_lines)
        
        # Update the peer list widget
        peer_list_widget = self.query_one("#peer-list", Static)
        peer_list_widget.update(peer_display)
    
    def get_peer_count(self) -> int:
        """Get the number of connected peers"""
        return len(self.peers)


class CommandInput(Container):
    """Command input area with buttons and text input"""
    
    class CommandSubmitted(Message):
        """Message sent when a command is submitted"""
        def __init__(self, command: str, args: str = ""):
            super().__init__()
            self.command = command
            self.args = args
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def compose(self):
        """Create the command input layout"""
        with Vertical():
            with Horizontal(classes="command-buttons"):
                yield Button("POST", id="btn-post", variant="primary")
                yield Button("DM", id="btn-dm", variant="default")
                yield Button("PROFILE", id="btn-profile", variant="default")
                yield Button("LIST", id="btn-list", variant="default")
                yield Button("VERBOSE", id="btn-verbose", variant="default")
                yield Button("QUIT", id="btn-quit", variant="error")
            
            yield Input(placeholder="Type your message or command here...", id="text-input")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        command = button_id.replace("btn-", "").upper()
        
        if command in ["POST", "DM", "PROFILE"]:
            # For these commands, we need text input
            text_input = self.query_one("#text-input", Input)
            args = text_input.value.strip()
            text_input.value = ""  # Clear input after use
            
            if command == "POST" and not args:
                self.post_message(self.CommandSubmitted("ERROR", "Please enter a message to broadcast"))
                return
            
            self.post_message(self.CommandSubmitted(command, args))
        else:
            # For LIST, VERBOSE, QUIT - no args needed
            self.post_message(self.CommandSubmitted(command))
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in text input"""
        args = event.value.strip()
        event.input.value = ""  # Clear input
        
        if args:
            # Default to POST command for direct text input
            self.post_message(self.CommandSubmitted("POST", args))


class StatusBar(Container):
    """Status bar showing connection info and stats"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = ""
        self.peer_count = 0
        self.verbose_mode = False
        self.local_address = ""
    
    def compose(self):
        """Create the status bar layout"""
        with Horizontal(classes="status-bar"):
            yield Static("Not connected", id="user-status", classes="status-item")
            yield Static("Peers: 0", id="peer-status", classes="status-item")
            yield Static("Verbose: OFF", id="verbose-status", classes="status-item")
            yield Static("", id="network-status", classes="status-item")
    
    def update_status(self, user_id: str = None, peer_count: int = None, 
                     verbose_mode: bool = None, local_address: str = None):
        """Update status bar information"""
        if user_id is not None:
            self.user_id = user_id
            self.query_one("#user-status", Static).update(f"User: {user_id}")
        
        if peer_count is not None:
            self.peer_count = peer_count
            self.query_one("#peer-status", Static).update(f"Peers: {peer_count}")
        
        if verbose_mode is not None:
            self.verbose_mode = verbose_mode
            mode_text = "ON" if verbose_mode else "OFF"
            self.query_one("#verbose-status", Static).update(f"Verbose: {mode_text}")
        
        if local_address is not None:
            self.local_address = local_address
            self.query_one("#network-status", Static).update(f"Listening: {local_address}")


class ProfileDialog(Container):
    """Dialog for profile creation/editing"""
    
    class ProfileSubmitted(Message):
        """Message sent when profile is submitted"""
        def __init__(self, display_name: str, status: str, avatar_path: str = ""):
            super().__init__()
            self.display_name = display_name
            self.status = status
            self.avatar_path = avatar_path
    
    class DialogClosed(Message):
        """Message sent when dialog is closed"""
        pass
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.display = False
    
    def compose(self):
        """Create the profile dialog layout"""
        with Vertical(classes="profile-dialog"):
            yield Label("Create/Update Profile", classes="dialog-title")
            yield Input(placeholder="Display Name", id="display-name-input")
            yield Input(placeholder="Status Message", id="status-input")
            yield Input(placeholder="Avatar File Path (optional)", id="avatar-input")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Save", id="save-profile", variant="primary")
                yield Button("Cancel", id="cancel-profile", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle profile dialog buttons"""
        if event.button.id == "save-profile":
            display_name = self.query_one("#display-name-input", Input).value
            status = self.query_one("#status-input", Input).value
            avatar_path = self.query_one("#avatar-input", Input).value
            
            self.post_message(self.ProfileSubmitted(display_name, status, avatar_path))
        elif event.button.id == "cancel-profile":
            self.post_message(self.DialogClosed())
    
    def show_dialog(self):
        """Show the profile dialog"""
        self.display = True
        self.styles.display = "block"
    
    def hide_dialog(self):
        """Hide the profile dialog"""
        self.display = False
        self.styles.display = "none"
        # Clear inputs
        self.query_one("#display-name-input", Input).value = ""
        self.query_one("#status-input", Input).value = ""
        self.query_one("#avatar-input", Input).value = ""


class DMDialog(Container):
    """Dialog for sending direct messages"""
    
    class DMSubmitted(Message):
        """Message sent when DM is submitted"""
        def __init__(self, recipient: str, message: str):
            super().__init__()
            self.recipient = recipient
            self.message = message
    
    class DialogClosed(Message):
        """Message sent when dialog is closed"""
        pass
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.display = False
        self.available_peers = []
    
    def compose(self):
        """Create the DM dialog layout"""
        with Vertical(classes="dm-dialog"):
            yield Label("Send Direct Message", classes="dialog-title")
            yield Static("Available peers:", classes="peer-list-label")
            yield Static("No peers available", id="dm-peer-list", classes="peer-list")
            yield Input(placeholder="Recipient (user@ip)", id="recipient-input")
            yield Input(placeholder="Your message", id="message-input")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Send", id="send-dm", variant="primary")
                yield Button("Cancel", id="cancel-dm", variant="default")
    
    def update_available_peers(self, peers: Dict[str, Dict]):
        """Update the list of available peers for DM"""
        self.available_peers = list(peers.keys())
        
        if not peers:
            peer_display = "No peers available"
        else:
            peer_lines = [f"• {user_id}" for user_id in peers.keys()]
            peer_display = "\n".join(peer_lines)
        
        self.query_one("#dm-peer-list", Static).update(peer_display)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle DM dialog buttons"""
        if event.button.id == "send-dm":
            recipient = self.query_one("#recipient-input", Input).value
            message = self.query_one("#message-input", Input).value
            
            if not recipient or not message:
                return  # TODO: Show error message
            
            self.post_message(self.DMSubmitted(recipient, message))
        elif event.button.id == "cancel-dm":
            self.post_message(self.DialogClosed())
    
    def show_dialog(self):
        """Show the DM dialog"""
        self.display = True
        self.styles.display = "block"
    
    def hide_dialog(self):
        """Hide the DM dialog"""
        self.display = False
        self.styles.display = "none"
        # Clear inputs
        self.query_one("#recipient-input", Input).value = ""
        self.query_one("#message-input", Input).value = ""
