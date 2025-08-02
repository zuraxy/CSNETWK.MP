# Test from https://wiki.python.org/moin/UdpCommunication
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 50999
BUFFER_SIZE = 4096

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
# sock.bind(('',UDP_PORT))
print(f"[+] Listening on UDP port {LSNP_PORT}")

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message: %s" % data)
