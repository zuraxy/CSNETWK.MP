# CSNETWK.MP

# LSNP over UDP - Peer-to-Peer Implementation

🌐 **SERVERLESS PEER-TO-PEER ARCHITECTURE** - No central server required!

## 🚨 IMPORTANT: This is a P2P System!
- **USE**: `python run_peer.py` for peer-to-peer communication
- 🔗 **No server needed**: Peers communicate directly with each other
- 🗑️ **Cleaned up**: Removed all legacy monolithic and client-server implementations

## Quick Start

### Modular Implementation (Clean Architecture)
```bash
# Terminal 1
python run_peer.py

# Terminal 2  
python run_peer.py

# Terminal 3
python run_peer.py
```

### Alternative Modular Launcher
```bash
# Terminal 1
python run_peer_modular.py

# Terminal 2  
python run_peer_modular.py

# Terminal 3
python run_peer_modular.py
```

### Test Peer Discovery
```bash
python peer/discover_peers_modular.py
```

### Run All Tests
```bash
cd testing
python run_all_tests.py
python test_modular_components.py
python compare_implementations.py
```

## Architecture

This implementation uses a **clean modular architecture** with separated concerns:

### Modular Implementation (`run_peer.py`) ⭐ **Production Ready**
- **Separated concerns**: 4 specialized modules  
- **Maintainable**: Easy to test, debug, and extend
- **Production-ready**: Clean architecture patterns
- **No central server** required
- **Direct peer communication** 
- **Automatic peer discovery** via UDP broadcast
- **Self-healing network** with timeout handling

### Modular Architecture Overview
```
UDPPeerModular
├── NetworkManager     # UDP sockets, broadcasting, communication
├── PeerManager        # Peer discovery, tracking, profiles  
├── MessageHandler     # Message processing, routing, sending
└── UserInterface      # Commands, input handling, display
```

### Discovery System Architecture
```
DiscoveryManager
├── ConnectivityTester # Network connectivity testing
├── NetworkScanner     # Peer discovery and scanning
└── CLI Interface      # Rich command-line options
```

## Features

### Core Commands
- **POST**: Broadcast messages to all discovered peers
- **DM**: Send direct messages to specific peers
- **DMLIST**: View direct message history with a specific peer
- **PROFILE**: Share profile (with optional avatar) with all peers
- **LIST**: Show all discovered peers on the network
- **FOLLOW/UNFOLLOW**: Follow or unfollow specific peers
- **FOLLOWING/FOLLOWERS**: View your following/followers lists
- **GROUP**: Create and manage group chats
- **GROUPVIEW**: View all your groups, members, and messages
- **FEED**: View your posts and liked posts
- **LIKE**: Like, unlike, and view likes on posts
- **VERBOSE**: Toggle between technical and user-friendly display
- **QUIT**: Exit the peer application

### Key Features
- 🔍 **Automatic Peer Discovery**: Peers find each other via UDP broadcast
- 💬 **Direct Communication**: No relay through central server
- 📷 **Avatar Support**: Profile pictures in base64 encoding
- 👥 **Group Chat**: Create groups, send messages to multiple peers simultaneously, and view detailed group overviews
- 👍 **Social Interactions**: Like/unlike posts and track engagement
- 🎮 **Games**: Built-in Rock Paper Scissors game with history tracking and leaderboard
- 🎛️ **Verbose/Clean Modes**: Technical details or user-friendly display
- 🌐 **Network Resilience**: Self-healing peer topology

## How It Works

### Peer Discovery
1. Each peer broadcasts presence announcements every 30 seconds
2. Peers respond to discovery messages from other peers
3. Each peer maintains a local list of discovered peers
4. Inactive peers are automatically removed after 5 minutes

### Message Flow
```
Peer A ────[broadcast]────► All Discovered Peers
Peer A ────[direct msg]───► Specific Peer B
```

### Network Topology
```
    Peer A ────── Peer B
      │ ╲       ╱  │
      │   ╲   ╱    │  
      │     ╲╱     │
    Peer D ────── Peer C
```

## Usage Examples

### Starting a Peer
```
Username: alice
Enable verbose mode? (y/n, default=y): n
Verbose mode: OFF
Peer started as alice@192.168.1.11
Listening on 192.168.1.11:8445

Commands: POST, DM, DMLIST, PROFILE, LIST, FOLLOW, UNFOLLOW, GROUP, GROUPVIEW, FEED, LIKE, VERBOSE, QUIT
```

### Broadcasting a Message
```
Command (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): POST
Message: Hello everyone!
Message broadcasted to 3 peers
```

### Direct Messaging
```
Command (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): DM
Available peers:
  - bob@192.168.1.12 (Bob Smith)
  - charlie@192.168.1.13 (Charlie Wilson)
Recipient (user@ip): bob@192.168.1.12
Message: Hey Bob, how are you?
DM sent to bob@192.168.1.12
```

### Viewing DM History
```
Command (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): DMLIST
Peers with DM history:
  1. bob@192.168.1.12 (Bob Smith) - 3 messages
  2. charlie@192.168.1.13 (Charlie Wilson) - 1 messages

Enter peer number or user@ip to view DMs: 1

===== Direct Messages with Bob Smith (bob@192.168.1.12) =====
[2025-08-10 14:32:15] You → Bob Smith: Hey Bob, how are you?
[2025-08-10 14:33:22] Bob Smith → You: I'm good, Alice! How about you?
[2025-08-10 14:35:05] You → Bob Smith: Doing great, thanks for asking!
===== End of Messages (3 total) =====
```

### Creating a Profile
```
Command (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): PROFILE
Display Name: Alice Johnson
Status message: Exploring P2P networking!
Add profile picture? (y/n): y
Enter path to image file: avatar.png
Avatar added: image/png, 1234 characters
Profile updated and broadcasted to 3 peers
```

### Viewing Group Overview
```
Command (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): GROUPVIEW

===== GROUP OVERVIEW =====
You are a member of 2 groups:

1. Project Team (ID: group123) (Creator)
   Members: 5 | Messages: 12
   Members:
     1. Alice Johnson (You) (Creator)
     2. Bob Smith
     3. Charlie Wilson
     4. Dana Lee
     5. Ethan Parks
   Recent Messages:
     [2025-08-10 15:22:45] Charlie Wilson: When is our next meeting?
     [2025-08-10 15:25:18] Bob Smith: Tomorrow at 3PM
     [2025-08-10 15:26:05] You: Perfect, I'll prepare the slides

2. Friends Chat (ID: group456)
   Members: 3 | Messages: 8
   Members:
     1. Alice Johnson (You)
     2. Bob Smith (Creator)
     3. Dana Lee
   Recent Messages:
     [2025-08-10 16:10:22] Dana Lee: Anyone free this weekend?
     [2025-08-10 16:11:45] You: I'm available Sunday afternoon!
     [2025-08-10 16:12:30] Bob Smith: Sunday works for me too

===== END OF GROUP OVERVIEW =====

View details of a specific group? Enter group number or ID (or press Enter to skip): 1

===== Project Team (ID: group123) =====
  1. View all members
  2. View all messages
  3. Send a message
  0. Back to group overview

Select option (0-3): 2

===== Messages in Project Team =====
[2025-08-10 14:45:12] Alice Johnson: Welcome to our project team!
[2025-08-10 14:50:33] Bob Smith: Thanks for setting this up, Alice!
[2025-08-10 15:05:22] Dana Lee: Excited to work with everyone!
[2025-08-10 15:10:45] Charlie Wilson: Let's get started on the planning
[2025-08-10 15:15:18] Ethan Parks: I'll share my notes from last session
[2025-08-10 15:20:30] Alice Johnson: Great idea, Ethan
[2025-08-10 15:22:45] Charlie Wilson: When is our next meeting?
[2025-08-10 15:25:18] Bob Smith: Tomorrow at 3PM
[2025-08-10 15:26:05] Alice Johnson: Perfect, I'll prepare the slides
===== End of Messages (9 total) =====
```

## File Structure

### Active P2P Implementation
```
peer/
├── udp_peer_modular.py      # Modular P2P peer implementation
├── discover_peers_modular.py # Modular peer discovery utility
├── modules/                 # Core P2P modules
│   ├── network_manager.py   # Network layer
│   ├── peer_manager.py      # Peer management
│   ├── message_handler.py   # Message processing
│   └── user_interface.py    # User interaction
├── discovery/               # Discovery system modules
│   ├── connectivity_tester.py
│   ├── network_scanner.py
│   └── discovery_manager.py
└── __init__.py

protocol/
├── protocol.py              # Message encoding/decoding
└── __init__.py

testing/
├── test_modular_*.py       # Modular architecture tests
├── test_*.py               # Feature tests
└── run_all_tests.py        # Test runner

run_peer.py                 # Main peer launcher (modular)
run_peer_modular.py         # Alternative modular launcher
markdowns/                  # Comprehensive documentation
```

### ✅ Legacy Files Completely Removed
```
All legacy monolithic and client-server files have been removed:
✅ No server/ directory
✅ No client/ directory  
✅ No run_server.py
✅ No run_client.py
✅ No monolithic implementations
✅ Clean modular architecture only
```

## Protocol Messages

### Existing Messages (Unchanged)
- **POST**: Broadcast messages
- **DM**: Direct messages between peers
- **PROFILE**: Profile updates with avatar support

### New P2P Messages
- **PEER_DISCOVERY**: Announce peer presence
- **PEER_LIST_REQUEST**: Request list of known peers
- **PEER_LIST_RESPONSE**: Response with peer information

## Testing

### Automated Testing
```bash
cd testing
python run_all_tests.py
```

### Manual Testing
```bash
# Test modular peer discovery
python peer/discover_peers_modular.py

# Start multiple peers in different terminals
python run_peer.py  # Repeat in multiple terminals

# Test commands: LIST, POST, DM, PROFILE
```

## Advantages Over Client-Server

**No Single Point of Failure**: No central server to crash  
**Better Scalability**: Direct peer communication  
**Reduced Latency**: No additional server hop  
**Decentralized**: No central authority required  
**Self-Healing**: Automatic peer discovery and recovery  

## Troubleshooting

### Peers Not Discovering Each Other
- Check firewall settings (allow UDP broadcast)
- Ensure peers are on same network
- Run discovery tool: `python peer/discover_peers_modular.py`

### Messages Not Delivered
- Use `LIST` command to verify peer discovery
- Check that target peer is still active
- Restart peers if needed

## Contributing

### Contributors
- DELA CRUZ, Karl Matthew B
- ESPINOSA, Jose Miguel  
- AQUINO, Bon Windel
- ENZO, Rafael Chan

### Architecture Migration
- Redesigned from client-server to peer-to-peer
- Maintained backward compatibility for message formats
- Added automatic peer discovery and direct communication

---

**Start the P2P network today with `python run_peer.py`!** 🚀