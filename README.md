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