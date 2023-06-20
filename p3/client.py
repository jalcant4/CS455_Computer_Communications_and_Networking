import socket
import select
from dataclasses import dataclass
import sys
import time

@dataclass
class client:
    node:   str
    port:   int
    sock:   socket
    dv:     list


# server is hosted here, and keeps track of dv
SERVER_ADDRESS = ('127.0.0.1', 8000)
BUFFER_SIZE = 1024

# nodes and ports
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}

# global variables
NODE_IP = 'localhost'                                                                                                    # 
ROUND_END = len(nodes)
TURN_ORDER = 0
MAX = 10000
N = len(nodes)

# turn variables
turn_counter = 0
round_counter = 0
clients = []
sockets = []


# files
client_log = open("client_log.txt", "w+")


def network_init():
    global clients, sockets
    # parse network.txt
    with open("network.txt", "r") as file:
        node_index = 0                                              
        for line in file:                                                               # each line in file represents a node
            line = [int(x) for x in line.split(" ")]                                    # line = "0 2 0 0 1" -> [0, 2, 0, 0, 1]
            for i, vector in enumerate(line):                                           # line = "0 2 0 0 1" -> [0, 2, MAX, MAX, 1]
                if i != node_index and vector == 0:    
                    line[i] = MAX   

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.bind((NODE_IP, ports[nodes[node_index]]))
            # Connect the socket to the port where the server is listening
            print(f"Node: {nodes[node_index]} is connecting to the server")
            client_socket.connect(SERVER_ADDRESS)

            sockets.append(client_socket)
            clients.append(client(node= nodes[node_index], port= ports[nodes[node_index]], sock= client_socket, dv= line))
            node_index += 1  

def client_init():
    global turn_counter, round_counter, TURN_ORDER

    turn_counter = 0
    round_counter = 1
    TURN_ORDER = 0


def client_action():
    readable, writable, _ = select.select([client.sock for client in clients], [client.sock for client in clients], [], 0.5)

    for client in readable:
        server_message = client.sock.recv(BUFFER_SIZE).decode()
        print(f"{server_message}")
        pass

    for sock in writable:
        while round_counter < ROUND_END:
            # 1. if a sender, then send
            if turn_counter == TURN_ORDER:                                                  # my turn to send
                for client in clients:                                                      # iterate through clients
                    if client.sock == sock:                                                      # if this is the sock, get client
                        break
                # Send data
                message = f"{client.node}:{client.dv}"
                print(f"Sending {message} to server")
                sock.sendall(message.encode())
                break


def main():
    try:
        network_init()
        client_init()
        client_action()
    finally:
        client_log.close()
        for each in clients:
            each.close()

if __name__ == "__main__":
    main()