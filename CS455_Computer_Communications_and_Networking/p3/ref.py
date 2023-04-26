# Here's a high-level outline of how you can implement the distributed distance vector
# routing (DVR) algorithm in Python:
# Create a function called network_init() that reads the network topology from the
# network.txt input file. The adjacency matrix in network.txt represents the weights
# of the links between nodes in the network. You can read this matrix and store it in
# a data structure, such as a 2D list, to represent the network topology.
# Based on the network topology, create N threads (one for each node) using Python's
# threading module. Each thread represents a node in the network.
# In each thread, implement the DV algorithm to calculate the shortest paths from 
# the current node to all other nodes in the network. Each node maintains (M+1) distance
# vectors, where M is the number of neighbors of the node. The distance vectors 
# represent the node's estimate of its cost to all destinations in the network. 
# The node updates its distance vectors based on the information received from its neighbors.
# Use TCP sockets to establish communication between neighboring nodes. Each node
# should have a TCP server socket to receive DV messages from its neighbors and
# a TCP client socket to send DV messages to its neighbors. You can use Python's
# socket module to implement the sockets.
# Implement the DV message sending order and stopping condition. For simplicity,
# assume that nodes send out DV messages in a strict order in each round 
# (e.g., A, B, C, D, E, A, B, C, D, E, ...). Each node sends its DV message to 
# its neighbors using its client socket, and receives DV messages from its neighbors
# using its server socket. The DV messages should contain the node's distance vectors,
# which are updated based on the information received from neighbors.
# Implement the convergence condition for the algorithm to stop. The algorithm should
# stop when the distance vectors of all nodes have converged, i.e., they are no longer changing.
# You may need to implement a global data structure, such as a shared socket table,
# that can be accessed by all threads to find the sockets of other nodes.
# Once the algorithm has converged, print the shortest paths from each node to all
# other nodes in the network.
# Note: This is a high-level outline and the actual implementation may require more
# details and error handling. Make sure to thoroughly test your implementation with different network topologies to ensure correctness.

import threading
import socket
import time

# Define constants
NUM_NODES = 5  # Number of nodes in the network
DV_SIZE = NUM_NODES  # Size of distance vectors
DV_UPDATE_INTERVAL = 1  # Interval for sending DV messages in seconds
DV_SEND_ORDER = ['A', 'B', 'C', 'D', 'E']  # Order for sending DV messages

# Define adjacency matrix for network topology
NETWORK_TOPOLOGY = [
    [0, 2, 0, 0, 1],
    [2, 0, 5, 0, 0],
    [0, 5, 0, 4, 0],
    [0, 0, 4, 0, 1],
    [1, 0, 0, 1, 0]
]

# Define DV messages data structure
dv_messages = {}
for node in DV_SEND_ORDER:
    dv_messages[node] = [float('inf')] * DV_SIZE
    dv_messages[node][ord(node) - ord('A')] = 0

#output will be like:   
#{
#   'A': [0.0, inf, inf],
#   'B': [inf, 0.0, inf],
#   'C': [inf, inf, 0.0]
# }
# This represents a distance vector with A, B, and C nodes, where the distance from each node to itself is 0, and the distance to all other nodes is initially unknown (represented by inf).

def send_dv_messages(node):
    """
    Function to send DV messages from a node to its neighbors.
    """
    while True:
        for neighbor, weight in NETWORK_TOPOLOGY[ord(node) - ord('A')]:
            # Create client socket for sending DV messages
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 5000 + ord(neighbor) - ord('A')))
            # Send DV message
            dv_message = ' '.join(str(cost) for cost in dv_messages[node])
            client_socket.sendall(dv_message.encode())
            client_socket.close()
        time.sleep(DV_UPDATE_INTERVAL)


def receive_dv_messages(node):
    """
    Function to receive DV messages from neighbors and update distance vectors.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5000 + ord(node) - ord('A')))
    server_socket.listen(5)

    while True:
        conn, addr = server_socket.accept()
        data = conn.recv(1024).decode()
        dv = [int(cost) for cost in data.split(' ')]
        dv_messages[node] = dv
        conn.close()


def network_init():
    """
    Function to initialize the network, create node threads, and start sending/receiving DV messages.
    """
    threads = []
    for node in DV_SEND_ORDER:
        # Create and start thread for sending DV messages
        t_send = threading.Thread(target=send_dv_messages, args=(node,))
        t_send.start()
        threads.append(t_send)

        # Create and start thread for receiving DV messages
        t_receive = threading.Thread(target=receive_dv_messages, args=(node,))
        t_receive.start()
        threads.append(t_receive)

    # Wait for all threads to finish
    for t in threads:
        t.join()


if __name__ == '__main__':
    network_init()
  
  
# This Python code implements a distributed algorithm for computing shortest paths in a network, based on the distance-vector algorithm.
# The network topology is represented by an adjacency matrix stored in the variable NETWORK_TOPOLOGY, where each row and column corresponds
# to a node in the network and the entries represent the edge weights between the nodes. The nodes are labeled 'A' through 'E'.

# The code initializes a distance vector dv_messages for each node in the network, with the initial distance from a node to itself being zero,
# and the distance to all other nodes being infinity. The distance vectors are stored as dictionaries, where the keys are the node labels and the values are lists of distances.

# The send_dv_messages function sends the distance vectors from a node to all its neighbors in the network, using TCP sockets. The function
# iterates over the neighbors of the node and for each neighbor, it creates a socket connection to the neighbor's IP address and port number,
# sends the distance vector over the socket connection, and closes the socket. The function then waits for a specified interval of time DV_UPDATE_INTERVAL before repeating the process.

# The receive_dv_messages function receives distance vectors from neighbors and updates the node's own distance vector accordingly.
# The function listens for incoming TCP connections on the node's IP address and port number, accepts the connection, receives the distance vector 
# from the connection, decodes it into a list of integers, and stores the list as the new distance vector for the node. The function then closes the connection and repeats the process.

# To use the code, you would need to start a process for each node in the network and call the send_dv_messages and receive_dv_messages functions for each node.
# The output of the code is not a single output but rather a continuously updated dictionary of distance vectors for each node. The code provided here initializes
# the distance vectors, but does not execute the algorithm or output any results.
##################################################################################3  
# Explanation:
#  Let me explain the code step by step:
# Import the required libraries: The code imports the threading, socket, and time libraries, which are used for creating and managing threads, sending/receiving data
# over sockets, and adding delays in the program, respectively.
# Define constants: The code defines several constants that are used in the network simulation. These constants include the number of nodes in the network (NUM_NODES), 
# the size of the distance vectors (DV_SIZE), the interval for sending DV messages (DV_UPDATE_INTERVAL), and the order for sending DV messages (DV_SEND_ORDER). 
# Additionally, the code defines the NETWORK_TOPOLOGY as an adjacency matrix, which represents the network topology with edge weights.
# Define DV messages data structure: The code initializes a dictionary dv_messages to store the distance vectors that will be sent as DV messages. 
# The keys in the dictionary are the nodes in the network (in the order defined by DV_SEND_ORDER), and the values are lists of size DV_SIZE representing 
# the distance vector for each node. The distance vector for a node is initially set to all infinity values, except for the cost from the node to itself, which is set to 0.
# Define functions for sending and receiving DV messages: The code defines two functions, send_dv_messages(node) and receive_dv_messages(node), which are responsible for
# sending and receiving DV messages, respectively. The send_dv_messages() function runs in a separate thread for each node and sends its distance vector to its neighbors using TCP sockets.
# The receive_dv_messages() function also runs in a separate thread for each node and listens for incoming DV messages from neighbors, updating its distance vector accordingly.
# Initialize the network and start threads: The network_init() function is called at the end of the code, which initializes the network by creating threads for sending and receiving 
# DV messages for each node in the network. The threads are started using the start() method, and their references are stored in a list threads. Finally, the code waits for all threads 
# to finish using the join() method.
# Main execution: The if __name__ == '__main__': block ensures that the network_init() function is only called if the code is being run as the main script. This is a common 
# Python idiom to prevent executing code meant for module import.
 ###############################################################################################################################################################   
    
import socket
import threading
import time

# Global variables
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}
DV = {}  # Distance vector table
lock = threading.Lock()
stop_flag = False  # Stop condition flag


def network_init():
    # Read and parse txt file to initialize distance vector table (DV)
    # and set initial distances between nodes
    with open('network.txt', 'r') as file:
        for line in file:
            node, neighbor, distance = line.split()
            if node not in DV:
                DV[node] = {}
            DV[node][neighbor] = int(distance)
            DV[node][node] = 0


def send_DV(node):
    # Send distance vector (DV) to neighboring nodes
    for neighbor in DV[node]:
        if neighbor != node:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', ports[neighbor]))
                message = f"{node}:{DV[node]}"                              
                sock.sendall(message.encode())
                sock.close()
            except ConnectionRefusedError:
                print(f"Failed to send DV from {node} to {neighbor}")


def update_DV(node, new_DV):
    # Update distance vector (DV) with new information
    with lock:
        if DV[node] != new_DV:
            DV[node] = new_DV
            return True
        else:
            return False


def calculate_new_DV(node):
    # Recalculate distance vector (DV) based on received DV from neighboring nodes
    new_DV = DV[node].copy()
    for neighbor in DV[node]:
        if neighbor != node:
            for dest in DV[neighbor]:
                if dest != node:
                    cost = DV[node][neighbor] + DV[neighbor][dest]
                    if dest not in new_DV or cost < new_DV[dest]:
                        new_DV[dest] = cost
    return new_DV


def receive_DV(node):
    # Receive distance vector (DV) from neighboring nodes
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', ports[node]))
    sock.listen(5)
    while not stop_flag:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        sender, received_DV = data.split(':')
        received_DV = eval(received_DV)
        conn.close()
        if update_DV(sender, received_DV):
            print(f"Node {node} received DV from {sender}")
            print(f"Updating DV at node {node}")
            print(f"New DV at node {node} = {DV[node]}")
            send_DV(node)  # Broadcast updated DV to neighboring nodes


def routing_algorithm():
    # Main routing algorithm logic
    rounds = 0
    while not stop_flag:
        for node in nodes:
            rounds += 1
            print(f"Round {rounds}: {node}")
            print(f"Current DV = {DV[node]}")
            last_DV = DV[node].copy()
            send_DV(node)  # Broadcast DV to neighboring nodes
            time.sleep(1)  # Wait for DV to propagate
            if not update_DV(node, calculate_new_DV(node)):
                print(f"No change in DV at node {node}")
            else:
                print(f"Updated DV at node {node} = {DV[node]}")
                time.sleep(5)  # Wait for all nodes to update their DV


if __name__ == '__main__':
    network_init()
    # Start thread for receiving DV from neighboring nodes
    receive_threads = []
    for node in nodes:
        t = threading.Thread(target=receive_DV, args=(node,))
        t.start()
        receive_threads.append(t)
    # Start main routing algorithm thread
    routing_thread = threading.Thread(target=routing_algorithm)
    routing_thread.start()
    # Wait for threads to complete
    for t in receive_threads:
        t.join()
    routing_thread.join()
    print("Routing algorithm stopped")
    
    
#     Explanation:
# Here is a step-by-step explanation of the code:
# The code imports necessary libraries: socket for network communication, threading for concurrent threads, and time for time-related operations.
# The code defines global variables:
# nodes: a list of node names in the network
# ports: a dictionary that maps node names to port numbers for communication
# DV: a distance vector table to store the distances between nodes
# lock: a threading lock to synchronize access to the DV table
# stop_flag: a boolean flag to stop the routing algorithm
# The code defines a function network_init() to read and parse a text file named network.txt which contains initial distance information between nodes.
# It initializes the DV table with the parsed information.

# The code defines a function send_DV(node) to send the distance vector of a node to its neighboring nodes. It iterates through the neighboring nodes
# of the given node and establishes a TCP connection with each neighbor to send the distance vector as a string.

# The code defines a function update_DV(node, new_DV) to update the DV table with new distance vector information received from neighboring nodes. 
# It uses a lock to synchronize access to the DV table to avoid race conditions. If the new distance vector is different from the current one, it updates
# the DV table and returns True, indicating that the DV table has been updated. Otherwise, it returns False.

# The code defines a function calculate_new_DV(node) to recalculate the distance vector of a node based on the received distance vectors from its neighboring
# nodes. It creates a copy of the current distance vector, and for each neighboring node, it calculates the cost of reaching other nodes through that neighbor.
# If the cost is lower than the current cost in the distance vector, it updates the distance vector with the new cost.

# The code defines a function receive_DV(node) to receive distance vectors from neighboring nodes. It creates a TCP socket, binds it to the local host and the
# port number associated with the given node, and listens for incoming connections. When a connection is established, it receives data from the connection, which 
# includes the sender node name and the received distance vector. It decodes the received data and updates the DV table using the update_DV() function. Then it
# closes the connection and repeats the process in a loop until the stop_flag is set.

# The code defines a function routing_algorithm() as the main logic of the distance vector routing algorithm. It runs in a loop until the stop_flag is set. For 
# each node in the network, it sends its current distance vector to its neighboring nodes using the send_DV() function, waits for a short duration for the distance 
# vectors to propagate, and then checks if there is any change in its own distance vector using the update_DV() function. If there is a change, it broadcasts the 
# updated distance vector to neighboring nodes again and waits for a longer duration for all nodes to update their distance vectors. This process repeats in each round.

# The code uses the if __name__ == '__main__': block to define the entry point of the program. It calls the network_init() function to initialize the DV table, starts
# threads for receiving distance vectors from neighboring nodes using the receive_DV() function, and starts the main routing algorithm thread using the routing_algorithm() function.
# Finally, it waits for all threads to complete using the join() method and prints a message indicating that the routing algorithm has stopped.