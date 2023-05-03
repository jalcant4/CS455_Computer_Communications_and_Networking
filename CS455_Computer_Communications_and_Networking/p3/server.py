# Written by Jed Mendoza G00846927

import select
import socket
import subprocess
import threading
import time

# server variables
SERVER_ADDRESS = ('127.0.0.1', 8000)
DV = {}                                                                                 # Distance vector table
MAX = 10000                                                                             # Assign Maximum distance
N = 0                                                                                   # Number of nodes
BUFFER_SIZE = 1024                                                                      # Largest buff size

# global variables
server_socket = None
turn_order = 0
round_counter = 1
lock = threading.Lock()

# nodes and ports
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}                         # ports of the connections
connections = []                                                                        # holds connections of the connections
    
# files
output = open("output.txt", "w+")
server_log = open("server_log.txt", "w+")
error_log = open("error_log.txt", "w+")


def network_init():
    global server_socket, N
    N = 0
    # parse network.txt
    with open('network.txt', 'r') as file:                                              
        for line in file:                                                               # each line in file represents a node
            DV[nodes[N]] = []
            line = [int(x) for x in line.split(" ")]                                    # line = "0 2 0 0 1" -> [0, 2, 0, 0, 1]
            
            line_length = len(line)
            for index in range(line_length):
                if line[index] != N and line[index] == 0:    
                    line[index] = MAX   
                index += 1

            args = ['python3', 'client.py', nodes[N], str(line)]
            subprocess.run(args)
            print(f"Starting subprocess: {args}", file= server_log)

            N += 1
        N -= 1                                                                          # Fix N


def server_init():
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    print(f"Starting up on {SERVER_ADDRESS[0]} Port {SERVER_ADDRESS[1]}", file= server_log)
    server_socket.bind(SERVER_ADDRESS)

    # Listen for incoming connections
    server_socket.listen(N)

    # Get connections
    num_conn = 0
    while num_conn < 1:
        
        print(f"Waiting for a connection", file= server_log)
        
        connection, client_address = server_socket.accept()
        for key, value in ports.items():
            if value == client_address[1]:
                client_node = key
        
        print(f"Client Node: {client_node}, Connection Address {client_address}", file= server_log)
        connections.append(connection)
        num_conn += 1


def server_action():
    global server_socket

    while round_counter < N:
        readable, _, _ = select.select(connections, [], [], 0.5)

        for connection in readable:
            try:
                # Receive the data then retransmit it
                data = connection.recv(BUFFER_SIZE)                                 # 2.
                if data:
                    print(f"Received {data.decode()}", file= server_log)

                    client_node, client_dv = data.split(":")
                    client_dv = [int(x) for x in client_dv[1:-1].split(",")]

                    print(f"Round {round_counter}: {client_node}")                  # 1. start the round
                    print(f"Current DV = {client_dv}")                              # 2. the dv the client sent is the current dv
                    last_dv = DV[nodes.index(client_node)]
                    print(f"Last DV = {last_dv}")                                   # 3. the dv in the server is the last dv
                    
                    update = (client_dv != last_dv)                                 # 4. check if it was updated
                    if update:
                        print(f"Updated from last DV or the same? Updated")

                        DV[nodes.index(client_node)] = client_dv
                    else:
                        print(f"Updated from last DV or the same? Same")

                    #print(f"Forwarding data to {}", file= server_log)
                    connection.sendall(data)
                    break
                # Let other connections    
                else:
                    print(f"No more data from {connection}", file= server_log)
                    connections.remove(connection)
                        
            except Exception as e:
                print(f"Connection: {connection} with Error: {e}", file= error_log)
            

    # end of server
    for each in connections:
        each.close()
    server_socket.close()

def forward_dv():
    pass

def update_dv(server_node, client_node, client_DV):
    global DV
    # given we are in Node A, we DV info from Node B
    # Old node:            {0 2 0 0 1}
    # client node:         {2 0 5 0 0}
    # New node:            {0 2 7 0 1}
    # Recalculate distance vector (DV) based on received DV from neighboring nodes
    server_index = nodes.index(server_node)                                             # a reference to self
    server_DV = DV[server_index]                                                
    dv_len = len(DV[server_index])

    client_index = nodes.index(client_node)
    client_offset = DV[server_index][client_index]
    with lock:
        for index in range(dv_len):
            if index != server_index:                                                   # if self dont update at server_index
                continue
            elif server_DV[index] > client_DV[index] + client_offset:                                                   
                server_DV[index] = client_DV[index] +  client_offset                    # To update the distance vector


def get_neighbors(client_node):
    neighbors = []
    client_dv = DV[nodes.index(client_node)]
    
    index = 0
    for neighbor in client_dv:
        if neighbor != 0 and neighbor < MAX:
            #print(f"Node {server_node} and my neighbor is {addresses[index]}")
            neighbors.append(index)
        index += 1  

    return neighbors

def main():
    global output
    try:
        # network_init()
        server_init()
        server_action()
    finally:
        output.close()
        server_log.close()

if __name__ == "__main__":
    main()