# Test from https://wiki.python.org/moin/UdpCommunication
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 50999
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT)) # should it be sock.bind(('',UDP_PORT)) instead
print(f"[+] Listening on UDP port {UDP_PORT}")

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE) # buffer size is 1024 bytes
    print("received message: %s" % data)
