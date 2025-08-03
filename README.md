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
- **PROFILE**: Share profile (with optional avatar) with all peers
- **LIST**: Show all discovered peers on the network
- **VERBOSE**: Toggle between technical and user-friendly display
- **QUIT**: Exit the peer application

### Key Features
- 🔍 **Automatic Peer Discovery**: Peers find each other via UDP broadcast
- 💬 **Direct Communication**: No relay through central server
- 📷 **Avatar Support**: Profile pictures in base64 encoding
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

Commands: POST, DM, PROFILE, LIST, VERBOSE, QUIT
```

### Broadcasting a Message
```
Command (POST/DM/PROFILE/LIST/VERBOSE/QUIT): POST
Message: Hello everyone!
Message broadcasted to 3 peers
```

### Direct Messaging
```
Command (POST/DM/PROFILE/LIST/VERBOSE/QUIT): DM
Available peers:
  - bob@192.168.1.12 (Bob Smith)
  - charlie@192.168.1.13 (Charlie Wilson)
Recipient (user@ip): bob@192.168.1.12
Message: Hey Bob, how are you?
DM sent to bob@192.168.1.12
```

### Creating a Profile
```
Command (POST/DM/PROFILE/LIST/VERBOSE/QUIT): PROFILE
Display Name: Alice Johnson
Status message: Exploring P2P networking!
Add profile picture? (y/n): y
Enter path to image file: avatar.png
Avatar added: image/png, 1234 characters
Profile updated and broadcasted to 3 peers
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