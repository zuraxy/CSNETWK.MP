# A.I. Disclaimer
This markdown is A.I. generated, but has been properly reviewed, verified, and revised according to the group's own comprehension.

# DM (Direct Message) Implementation Guide

## Overview
The DM functionality has been implemented according to the RFC specifications. 
Through this functionality, users should are given the ability to private message other users as specific recipients.

## Features Implemented

### 1. DM Message Format
- **TYPE**: DM
- **FROM**: Sender's user ID (username@ip)
- **TO**: Recipient's user ID (username@ip)
- **CONTENT**: The message content
- **TIMESTAMP**: Unix timestamp when message was created
- **MESSAGE_ID**: Unique 64-bit hex identifier                                  (*have to recheck this - might need to reduce to 32-bits because it's only 8 hex in RFC)
- **TOKEN**: Authorization token with format `user_id|timestamp+ttl|chat`       (*recheck if tokens are allowed in Milestone 1)

### 2. Server Functionality
- **User Tracking**: Tracks clients and their user IDs
- **Message Routing**: Routes DM messages to specific recipients (sent over unicast)
- **Error Handling**: Returns error if recipient is not found/offline
- **User Listing**: Provides list of online users thru "LIST"

### 3. Client Functionality
- **DM Sending**: Interactive DM composition and sending
- **Message Display**: Differentiated display for DMs, POSTs, and errors
- **User Listing**: Command to see who's online thru "LIST"
- **Error Feedback**: Shows delivery errors

### 4. Error Handling
- **Recipient Offline**: Server returns error message to sender
- **Invalid Format**: Server handles gracefully
- **Network Issues**: Connection errors are logged and clients cleaned up

### 5. Security Features
- **Token-based Authorization**: Each message includes authorization token              (*quite problematic since milestone 1 should not include this?)
- **Scoped Permissions**: DM tokens scoped for 'chat', POST tokens for 'broadcast'      (*quite problematic since milestone 1 should not include this?)
- **TTL**: Messages include time-to-live for expiration                                 (*quite problematic since milestone 1 should not include this?)

## Test and Usage Instructions

### Testing
Run `python test_dm.py` to verify message format compliance with RFC specifications.

The implementation follows the RFC document with error handling and user management.

### Freestyle usage/testing
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