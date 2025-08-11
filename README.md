# CSNETWK.MP

# LSNP over UDP - Peer-to-Peer Implementation

🌐 **SERVERLESS PEER-TO-PEER ARCHITECTURE** - No central server required!

## 🚨 IMPORTANT: This is a P2P System!
- **USE**: `python run_peer.py` for peer-to-peer communication
- 🔗 **No server needed**: Peers communicate directly with each other

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

## Architecture

This implementation uses a **clean modular architecture** with separated concerns:

### Modular Implementation (`run_peer.py`) 
- **Separated concerns**
- **Maintainable**: Easy to test and debug
- **Production-ready**: Clean architecture patterns
- **No central server** required
- **Direct peer communication** 
- **Automatic peer discovery** via UDP broadcast
  
## Features

### Core Commands
- **POST**: Broadcast messages to all discovered peers
- **DM**: Send direct messages to specific peers
- **DMLIST**: View direct message history with a specific peer
- **PROFILE**: Share profile (with optional avatar) with all peers
- **LIST**: Show all discovered peers on the network
- **FOLLOW/UNFOLLOW**: Follow or unfollow specific peers
- **GROUP**: Create and manage group chats
- **LIKE**: Like, unlike, and view likes on posts
- **VERBOSE**: Toggle between technical and user-friendly display
- **GAME**: Play Tic Tac Toe
- **FILE**: Send files to peer
- **QUIT**: Exit the peer application

### Key Features
- 🔍 **Automatic Peer Discovery**: Peers find each other via UDP broadcast
- 💬 **Direct Communication**: No relay through central server
- 📷 **Avatar Support**: Profile pictures in base64 encoding
- 👥 **Group Chat**: Create groups, send messages to multiple peers simultaneously
- 👍 **Social Interactions**: Like/unlike posts
- 🎮 **Games**: Built-in Tic Tac Toe game 
- 🎛️ **Verbose/Clean Modes**: Technical details or user-friendly display

### AI Disclosure
- AI tools such as ChatGPT and CoPilot were used during the development of this project to assist in understanding protocol requirements and generating portions of the codebase. All AI-generated content, including code and explanations, was reviewed, tested, and verified by the student to ensure correctness, compliance with project specifications, and adherence to academic integrity.

### Contributors
- AQUINO, Bon Windel
- CHAN, Enzo Rafael
- DELA CRUZ, Karl Matthew 
- ESPINOSA, Jose Miguel  
