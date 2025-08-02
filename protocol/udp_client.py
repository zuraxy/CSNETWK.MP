# 
import socket
import threading
import random
import secrets
import time
from protocol import Protocol

encode_message = Protocol.encode_message
decode_message = Protocol.decode_message

client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

name = input("User: ")

# Receives messages that is threaded
def receive():
    while True:
        try:
            message, _ = client.recvfrom(1024)
            print(message.decode())
        except:
            pass
t = threading.Thread(target=receive)
t.start()

# First send to server
client.sendto(f"SIGNUP_TAG:{name}".encode(),("localhost",50999))

#Gets local ip, returns local ip
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
# generates a 64 bit binary in hext format
def generate_message_id():  
    return secrets.token_hex(8)


# This is main loop for sending messages
while  True:
    user_address = get_local_ip()
    
    msg_type = input("What do you want to use (POST/PROFILE/DM): ").strip().upper()
    # Multiple if checks to determine what format to use for verbose 
    if msg_type == "POST":
        msg = input("Message: ")
        msg_id = generate_message_id()
        timestamp = int(time.time())
        user_id = name+'@'+user_address
        time_and_ttl = 3600+timestamp
        data = {
            'TYPE':'POST',
            'USER_ID':f'{user_id}',
            'CONTENT':f'{msg}',
            'TTL':'3600',
            'MESSAGE_ID' :f'{msg_id}',
            'TOKEN': f'{user_id}|{time_and_ttl}|broadcast'
              }
    elif msg_type == "PROFILE":
        exit()
    elif msg_type == "DM":
        exit()

    client.sendto(encode_message(data), ("localhost", 50999))
