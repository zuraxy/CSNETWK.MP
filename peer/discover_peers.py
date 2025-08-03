#!/usr/bin/env python3
"""
Simple peer discovery utility for testing P2P network
This script helps discover and test connectivity with peers
"""
import socket
import sys
import os
import time

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol.protocol import Protocol

def scan_for_peers():
    """Scan for peers on the network"""
    print("Scanning for P2P peers...")
    
    # Create socket for discovery
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2.0)
    
    # Discovery message
    discovery_msg = {
        'TYPE': 'PEER_DISCOVERY',
        'USER_ID': 'scanner@127.0.0.1',
        'PORT': '9999',
        'TIMESTAMP': str(int(time.time())),
        'MESSAGE_ID': 'scan123'
    }
    
    try:
        # Send broadcast discovery
        encoded = Protocol.encode_message(discovery_msg)
        sock.sendto(encoded, ('255.255.255.255', 50999))
        sock.sendto(encoded, ('127.0.0.1', 50999))
        
        print("Discovery broadcast sent, listening for responses...")
        
        # Listen for responses
        peers_found = []
        start_time = time.time()
        
        while time.time() - start_time < 5.0:  # Listen for 5 seconds
            try:
                data, addr = sock.recvfrom(65536)
                try:
                    msg = Protocol.decode_message(data)
                    if msg.get('TYPE') == 'PEER_DISCOVERY':
                        user_id = msg.get('USER_ID', 'Unknown')
                        port = msg.get('PORT', 'Unknown')
                        if user_id != 'scanner@127.0.0.1':  # Don't count ourselves
                            peer_info = f"{user_id} at {addr[0]}:{port}"
                            if peer_info not in peers_found:
                                peers_found.append(peer_info)
                                print(f"Found peer: {peer_info}")
                except:
                    pass
            except socket.timeout:
                continue
            except:
                break
        
        print(f"\nScan complete. Found {len(peers_found)} peers:")
        for i, peer in enumerate(peers_found, 1):
            print(f"  {i}. {peer}")
        
        if not peers_found:
            print("No peers found. Make sure peers are running and discoverable.")
            
    except Exception as e:
        print(f"Error during scan: {e}")
    finally:
        sock.close()

def test_connectivity():
    """Test basic UDP connectivity"""
    print("\nTesting UDP connectivity...")
    
    # Test local loopback
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 0))
        local_port = sock.getsockname()[1]
        
        # Send test message to ourselves
        test_msg = b"UDP_TEST"
        sock.sendto(test_msg, ('127.0.0.1', local_port))
        sock.settimeout(1.0)
        
        data, addr = sock.recvfrom(1024)
        if data == test_msg:
            print("Local UDP connectivity: OK")
        else:
            print("Local UDP connectivity: FAILED")
            
        sock.close()
        
    except Exception as e:
        print(f"Local UDP connectivity: FAILED ({e})")
    
    # Test broadcast capability
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"BROADCAST_TEST", ('255.255.255.255', 50999))
        sock.close()
        print("Broadcast capability: OK")
    except Exception as e:
        print(f"Broadcast capability: FAILED ({e})")

def main():
    """Main function"""
    print("P2P Network Discovery Tool")
    print("=" * 40)
    
    # Test basic connectivity first
    test_connectivity()
    
    print()
    
    # Scan for peers
    scan_for_peers()
    
    print("\nTo start a peer, run: python run_peer.py")
    print("To start multiple peers, run the command in separate terminals")

if __name__ == "__main__":
    main()
