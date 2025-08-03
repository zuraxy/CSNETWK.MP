# Test from https://wiki.python.org/moin/UdpCommunication
import socket
import threading
import queue
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

encode_message = Protocol.encode_message
decode_message = Protocol.decode_message

messages = queue.Queue()
clients = []
ttl_seconds = 3600

server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

server.bind(("localhost", 50999))

def receive():
    while True:
        try:
            message,addr = server.recvfrom(1024)
            messages.put((message,addr))
        except:
            pass


def broadcast():
    while True:
        while not messages.empty():
            message,addr = messages.get()
            print(message.decode())
            if addr not in clients:
                clients.append(addr)
            msg_dict = decode_message(message)
            # This checks if TTL is in the msg and appends a an expiration time default 3600 
            if 'TTL' in msg_dict:
                msg_dict['TTL'] = '3600'
                message = encode_message(msg_dict)
            for client in clients: 
                try:
                    if message.decode().startswith("SIGNUP_TAG:"):
                        name = message.decode()[message.decode().index(":")+1:]
                        print(f"{name} joined.") 
                    else:
                        server.sendto(message,client)
                except:
                    clients.remove(client)

t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=broadcast)

t1.start()
t2.start()