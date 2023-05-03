import socket
import sys
import time

# server is hosted here, and keeps track of dv
SERVER_ADDRESS = ('127.0.0.1', 8000)
BUFFER_SIZE = 1024

# nodes and ports
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}

# global variables
NODE_NAME = None                                                        # the name of the node
NODE_PORT = None                                                        # the port
NODE_IP = 'localhost'                                                   # the ip
DV = [0, 2, 0, 0, 1]                                                    # 
ROUND_END = len(nodes)
TURN_ORDER = None
MAX = 10000

# turn variables
client_socket = None
turn_counter = 0
round_counter = 1

def client_init():
    global turn_counter, round_counter, client_socket, NODE_NAME, NODE_PORT, TURN_ORDER
    NODE_NAME = sys.argv[1]
    NODE_PORT = ports[NODE_NAME]
    TURN_ORDER = nodes.index(NODE_NAME)
    DV = [int(x) for x in sys.argv[2:]]

    # wait for network
    time.sleep(5)

    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((NODE_IP, NODE_PORT))


def client_action():
    global client_socket
    # Connect the socket to the port where the server is listening
    print(f"Connecting to {SERVER_ADDRESS[0]} Port {SERVER_ADDRESS[1]}")
    client_socket.connect(SERVER_ADDRESS)

    try:
        while round_counter < ROUND_END:
            # 1. if a sender, then send
            if turn_counter == TURN_ORDER:   
                # Send data
                message = f"{NODE_NAME}:{DV}"
                print(f"Sending {message} to server")
                client_socket.sendall(message.encode())

            # 2. Wait for a response from server to update
            data = client_socket.recv(BUFFER_SIZE).decode().split(":")
            print(f"{data}")
                

    finally:
        print(f"Closing socket")
        client_socket.close()

def main():
    try:
        client_init()
    finally:
        pass

if __name__ == "__main__":
    main()