# Test from https://wiki.python.org/moin/UdpCommunication
import socket
import threading
import random

client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))
name = input("Nickname: ")
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

# This is main loop for sending messages
while  True:
    user_address = get_local_ip()
    
    msg_type = input("What do you want to use (POST/PROFILE/DM): ").strip().upper()
    # Multiple if checks to determine what format to use for verbose 
    if msg_type == "POST":
        msg = input("Message: ")
        data = {
            'TYPE':'POST',
            'USER_ID':'{name}@{user_address}',
            'CONTENT':'{msg}',
            'TTL':''
              }
    message = input("")
    if message == "PROFILE":
        exit()
    if message == "DM":
        exit()
    else:
        client.sendto(f"{name}: {message}".encode(),("localhost",50999))
