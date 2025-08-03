# DM (Direct Message) Implementation Guide

## Overview
The DM functionality has been successfully implemented according to the RFC specifications. Users can now send private messages directly to specific recipients.

## Features Implemented

### 1. DM Message Format
- **TYPE**: DM
- **FROM**: Sender's user ID (username@ip)
- **TO**: Recipient's user ID (username@ip)
- **CONTENT**: The message content
- **TIMESTAMP**: Unix timestamp when message was created
- **MESSAGE_ID**: Unique 64-bit hex identifier
- **TOKEN**: Authorization token with format `user_id|timestamp+ttl|chat`

### 2. Server Functionality
- **User Registration**: Tracks clients and their user IDs
- **Message Routing**: Routes DM messages to specific recipients (unicast)
- **Error Handling**: Returns error if recipient is not found/offline
- **User Listing**: Provides list of online users

### 3. Client Functionality
- **DM Sending**: Interactive DM composition and sending
- **Message Display**: Differentiated display for DMs, POSTs, and errors
- **User Listing**: Command to see who's online
- **Error Feedback**: Shows delivery errors

## Usage Instructions

### Starting the Application
1. **Start Server**: `python run_server.py`
2. **Start Client(s)**: `python run_client.py` (in separate terminals)

### Client Commands
1. **POST**: Broadcast message to all connected users
2. **DM**: Send private message to specific user
3. **LIST**: View all online users
4. **PROFILE**: Exit the application

### DM Workflow
1. Choose "DM" from the menu
2. Enter recipient in format `username@ip` (e.g., `bob@192.168.1.12`)
3. Type your message
4. Message is sent privately to the recipient only

### Example DM Session
```
What do you want to use (POST/PROFILE/DM/LIST): DM
Recipient (username@ip): bob@192.168.1.12
Message: Hi Bob, how are you?

[Server routes message to bob@192.168.1.12 only]
```

## Technical Details

### Message Flow
1. Client creates DM with all required fields
2. Server receives DM and identifies recipient
3. Server looks up recipient's address in client registry
4. Server sends message directly to recipient (unicast)
5. If recipient not found, server sends error back to sender

### Error Handling
- **Recipient Offline**: Server returns error message to sender
- **Invalid Format**: Server handles gracefully
- **Network Issues**: Connection errors are logged and clients cleaned up

### Security Features
- **Token-based Authorization**: Each message includes authorization token
- **Scoped Permissions**: DM tokens scoped for 'chat', POST tokens for 'broadcast'
- **TTL**: Messages include time-to-live for expiration

## Differences from POST
- **POST**: Broadcast to all clients except sender
- **DM**: Unicast to specific recipient only
- **Token Scope**: POST uses 'broadcast', DM uses 'chat'
- **Error Handling**: DM provides delivery confirmation/errors

## Testing
Run `python test_dm.py` to verify message format compliance with RFC specifications.

The implementation follows the RFC document exactly and provides a complete direct messaging system with proper error handling and user management.
