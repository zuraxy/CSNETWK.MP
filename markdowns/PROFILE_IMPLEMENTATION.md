# A.I. Disclaimer
This markdown is A.I. generated, but has been reviewed, verified, and revised according to the group's own comprehension.


# PROFILE Implementation Guide

## Overview
The PROFILE functionality has been implemented following the RFC specifications. Through this feature, users are given the ability to announce their identity to the network, including their chosen display name, status, and optionally, their profile picture.

## Features Implemented

### 1. PROFILE Message Format (RFC Compliant)
- **TYPE**: Always PROFILE
- **USER_ID**: Unique sender address (username@ipaddress)
- **DISPLAY_NAME**: User's public name
- **STATUS**: Short message or mood
- **AVATAR_TYPE**: MIME type of the image (optional)
- **AVATAR_ENCODING**: Currently always base64 (optional)
- **AVATAR_DATA**: Image data encoded as base64, under ~20KB (optional)
- **TIMESTAMP**: Unix timestamp when profile was created
- **MESSAGE_ID**: Unique identifier                                              (*should be removed)
- **TOKEN**: Authorization token with format `user_id|timestamp+ttl|profile`     (*should be removed)

### 2. Server Functionality
- **Profile Broadcasting**: Broadcasts PROFILE messages to all connected clients
- **Large Message Support**: Increased buffer size to handle avatar data (65KB)
- **Avatar Handling**: Properly processes and forwards avatar data
- **Logging**: Detailed logging of profile updates and avatar information

### 3. Client Functionality
- **Profile Creation**: Interactive profile setup with display name and status
- **Avatar Support**: Optional avatar upload with file validation
- **File Size Checking**: Warns if avatar exceeds 20KB recommendation
- **MIME Type Detection**: Automatic detection of image types
- **Profile Display**: Shows incoming profile updates from other users
- **Avatar Information**: Displays avatar type and encoding info

## Usage Instructions

### Creating/Updating Your Profile
1. Choose "PROFILE" from the main menu
2. Enter your display name (or press Enter to use username)
3. Enter a status message (or press Enter for default)
4. Choose whether to add a profile picture (y/n)
5. If adding avatar:
   - Enter path to image file
   - System validates file size and type
   - Avatar is encoded and included in profile

### Example Profile Session
```
What do you want to use (POST/PROFILE/DM/LIST): PROFILE
Display Name: Alice Johnson
Status message: Exploring the network!
Add profile picture? (y/n): y
Enter path to image file (or press Enter to skip): test_avatar.png
Avatar added: image/png, 96 characters
Profile created for Alice Johnson (alice@192.168.1.11)
```

### Viewing Other Users' Profiles
When other users update their profiles, you'll see:
```
[PROFILE UPDATE] Dave (dave@192.168.1.10)
  Status: Exploring LSNP!
  Avatar: image/png (base64 encoded)
```

## Technical Details

### Avatar Handling
- **Supported Formats**: Any image format supported by Python's `mimetypes` module
- **Size Limit**: Recommends under 20KB, warns for larger files
- **Encoding**: Base64 encoding as per RFC
- **Fallback**: Defaults to `image/png` if MIME type detection fails
- **Error Handling**: Graceful handling of missing files or encoding errors

### Message Broadcasting
- **Scope**: PROFILE messages are broadcast to ALL connected clients
- **Token**: Uses 'profile' scope in authorization token
- **Delivery**: Includes sender in broadcast for confirmation
- **Error Recovery**: Removes failed clients from broadcast list

### Backward Compatibility
- **Hosts without avatar support**: Can receive and process PROFILE messages
- **Avatar fields ignored**: AVATAR_* keys are simply disregarded by non-supporting clients
- **Core functionality preserved**: Display name and status work regardless of avatar support

### Network Considerations
- **Buffer Size**: Increased to 65KB to handle avatar data
- **Message Size**: Monitors and reports large message sizes
- **UDP Limits**: Ensures messages stay within practical UDP limits
- **Fragmentation**: Large avatars may be subject to IP fragmentation

## File Structure Changes

### New Dependencies
```python
import base64      # For avatar encoding
import mimetypes   # For MIME type detection
```

### Buffer Size Updates
- Client receive buffer: 1024 → 65536 bytes
- Server receive buffer: 1024 → 65536 bytes

## Testing

### Run Profile Tests
```bash
python test_profile.py
```

### Create Test Avatar
```bash
python create_test_avatar.py
```

### Manual Testing Workflow
1. Start server: `python run_server.py`
2. Start multiple clients: `python run_client.py`
3. Create profiles with different configurations:
   - Profile without avatar
   - Profile with small avatar
   - Profile with large avatar (test warning)
4. Verify all clients receive profile updates

## Security Considerations

### Avatar Security
- **File Size Validation**: Prevents extremely large files
- **MIME Type Validation**: Basic validation of image types
- **No File Execution**: Avatar data is only transmitted, not executed
- **Base64 Encoding**: Safe text-based transmission

### Token Authorization
- **Profile Scope**: Tokens scoped specifically for 'profile' operations
- **TTL**: Time-to-live prevents token reuse
- **User Binding**: Tokens tied to specific user ID

## Limitations and Future Enhancements

### Current Limitations
- No avatar compression
- No image format conversion
- Basic MIME type detection
- No avatar caching on client side

### Potential Enhancements
- Image resizing/compression before transmission
- Avatar caching to reduce network traffic
- Support for animated avatars
- Profile picture thumbnails
- Rich text status messages

## RFC Compliance

The implementation fully complies with the provided RFC specification:
- ✅ All required fields (TYPE, USER_ID, DISPLAY_NAME, STATUS)
- ✅ All optional fields (AVATAR_TYPE, AVATAR_ENCODING, AVATAR_DATA)
- ✅ Proper field formatting and naming
- ✅ Base64 encoding for avatar data
- ✅ MIME type metadata
- ✅ Backward compatibility for non-avatar-supporting hosts
- ✅ Broadcast behavior for network discovery
