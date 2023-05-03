import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print(f"starting up on {server_address[0]} port {server_address[1]}")
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print(f"waiting for a connection")
    connection, client_address = sock.accept()

    try:
        print(f"connection from {client_address}")

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(16)
            print(f"received {data.decode()}")
            if data:
                print(f"sending data back to the client")
                connection.sendall(data)
            else:
                print(f"no more data from {client_address}")
                break
            
    finally:
        # Clean up the connection
        connection.close()