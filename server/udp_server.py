# Test from https://wiki.python.org/moin/UdpCommunication
import socket
import threading
import queue
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

PORT_NUMBER = 50999

encode_message = Protocol.encode_message
decode_message = Protocol.decode_message

messages = queue.Queue()
clients = []  # List of (address, user_id) tuples
client_addresses = {}  # Dictionary mapping user_id to address
ttl_seconds = 3600

server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

server.bind(("localhost", PORT_NUMBER))
print(f"Server initially bound to port {PORT_NUMBER}")

def receive():
    while True:
        try:
            message,addr = server.recvfrom(65536)  # Increased buffer size for avatar data
            messages.put((message,addr))
        except:
            pass


def broadcast():
    while True:
        while not messages.empty():
            message, addr = messages.get()
            print(f"Received: {message.decode()}")
            
            # Handle signup messages
            if message.decode().startswith("SIGNUP_TAG:"):
                name = message.decode()[message.decode().index(":")+1:]
                user_id = f"{name}@{addr[0]}"
                
                # Add client if not already present
                if addr not in [client[0] for client in clients]:
                    clients.append((addr, user_id))
                    client_addresses[user_id] = addr
                    print(f"{name} ({user_id}) joined from {addr}")
                continue
            
            try:
                msg_dict = decode_message(message)
                msg_type = msg_dict.get('TYPE', '')
                
                # Handle POST messages (broadcast to all clients)
                if msg_type == 'POST':
                    print(f"Broadcasting POST from {msg_dict.get('USER_ID', 'unknown')}")
                    # Set TTL if present
                    if 'TTL' in msg_dict:
                        msg_dict['TTL'] = '3600'
                        message = encode_message(msg_dict)
                    
                    # Send to all clients except sender
                    sender_addr = addr
                    for client_addr, client_id in clients:
                        try:
                            if client_addr != sender_addr:  # Don't send back to sender
                                server.sendto(message, client_addr)
                        except Exception as e:
                            print(f"Error sending to {client_id}: {e}")
                            # Remove failed client
                            if (client_addr, client_id) in clients:
                                clients.remove((client_addr, client_id))
                                if client_id in client_addresses:
                                    del client_addresses[client_id]
                
                # Handle DM messages (send to specific recipient)
                elif msg_type == 'DM':
                    from_user = msg_dict.get('FROM', '')
                    to_user = msg_dict.get('TO', '')
                    content = msg_dict.get('CONTENT', '')
                    
                    print(f"DM from {from_user} to {to_user}: {content}")
                    
                    # Find recipient address
                    if to_user in client_addresses:
                        recipient_addr = client_addresses[to_user]
                        try:
                            server.sendto(message, recipient_addr)
                            print(f"DM delivered to {to_user} at {recipient_addr}")
                        except Exception as e:
                            print(f"Error delivering DM to {to_user}: {e}")
                    else:
                        # Recipient not found - could send error back to sender
                        error_msg = {
                            'TYPE': 'ERROR',
                            'MESSAGE': f'User {to_user} not found or offline',
                            'ORIGINAL_TO': to_user
                        }
                        try:
                            server.sendto(encode_message(error_msg), addr)
                            print(f"Sent error message to {from_user}: {to_user} not found")
                        except Exception as e:
                            print(f"Error sending error message: {e}")
                
                # Handle LIST_USERS messages
                elif msg_type == 'LIST_USERS':
                    from_user = msg_dict.get('FROM', '')
                    print(f"List users request from {from_user}")
                    
                    # Create list of online users
                    user_list = [client_id for _, client_id in clients]
                    user_list_str = ', '.join(user_list) if user_list else 'No users online'
                    
                    list_response = {
                        'TYPE': 'USER_LIST',
                        'USERS': user_list_str,
                        'COUNT': str(len(user_list))
                    }
                    
                    try:
                        server.sendto(encode_message(list_response), addr)
                        print(f"Sent user list to {from_user}: {user_list_str}")
                    except Exception as e:
                        print(f"Error sending user list: {e}")
                
                # Handle PROFILE messages (broadcast to all clients)
                elif msg_type == 'PROFILE':
                    user_id = msg_dict.get('USER_ID', '')
                    display_name = msg_dict.get('DISPLAY_NAME', 'Unknown')
                    status = msg_dict.get('STATUS', '')
                    has_avatar = 'AVATAR_DATA' in msg_dict
                    
                    print(f"Profile update from {display_name} ({user_id})")
                    if has_avatar:
                        avatar_type = msg_dict.get('AVATAR_TYPE', 'image/png')
                        avatar_size = len(msg_dict.get('AVATAR_DATA', ''))
                        print(f"  - Avatar: {avatar_type} ({avatar_size} chars)")
                    print(f"  - Status: {status}")
                    
                    # Broadcast profile to all clients (including sender for confirmation)
                    sender_addr = addr
                    successful_broadcasts = 0
                    
                    for client_addr, client_id in clients:
                        try:
                            server.sendto(message, client_addr)
                            successful_broadcasts += 1
                        except Exception as e:
                            print(f"Error broadcasting profile to {client_id}: {e}")
                            # Remove failed client
                            if (client_addr, client_id) in clients:
                                clients.remove((client_addr, client_id))
                                if client_id in client_addresses:
                                    del client_addresses[client_id]
                    
                    print(f"Profile broadcasted to {successful_broadcasts} clients")
                
                else:
                    print(f"Unknown message type: {msg_type}")
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                # If it's not a valid protocol message, treat as raw message
                for client_addr, client_id in clients:
                    try:
                        if client_addr != addr:  # Don't send back to sender
                            server.sendto(message, client_addr)
                    except Exception as send_e:
                        print(f"Error sending raw message to {client_id}: {send_e}")
                        if (client_addr, client_id) in clients:
                            clients.remove((client_addr, client_id))
                            if client_id in client_addresses:
                                del client_addresses[client_id]

t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=broadcast)

t1.start()
t2.start()