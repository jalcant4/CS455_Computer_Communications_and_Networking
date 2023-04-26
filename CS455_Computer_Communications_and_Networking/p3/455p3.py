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
    threads = []
    # Read and parse txt file to initialize distance vector table (DV)
    # and set initial distances between nodes
    with open('network.txt', 'r') as file:
        node = 0
        for line in file:                           # for each line
            line = line.split(" ")                  # "0 2 0 0 1" -> {"0", "2", "0", "0", "1"}
            line_len = len(line)

            DV[node] = {}                            # init a new node
            for edge in range(line_len):             # access each individual element in line
                DV[node][edge] = int(line[edge])       # assign DV[node][edge] to respective line[edge]

            # Create and start thread for sending DV messages TODO
            t_send = threading.Thread(target=send_dv_messages, args=(node,))
            t_send.start()
            threads.append(t_send)

            # Create and start thread for receiving DV messages TODO
            t_receive = threading.Thread(target=receive_dv_messages, args=(node,))
            t_receive.start()
            threads.append(t_receive)
            
            # add a new node for each new line
            node += 1                                

        # wait for all threads to end
        for t in threads:
            t.join()


def send_dv_messages(node):
    node_index = nodes.index(node)                                                      # node_index = 0 if 'A' ... 4 if 'E'

    N = len(DV[node_index])
    for dv_index in range(N):                                                           # iterate through each edge of the node
        if dv_index != node_index:                                                      # if not self
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                neighbor_node = nodes[dv_index]                                         # attempt to retrieve neighbor
                neighbor_port = ports[neighbor_node]                                    # retrieve Port No. of neighbor    
                neighbor_address = ('localhost', neighbor_port)                         # define neighbor address

                client_socket.connect(neighbor_address)                                 # connect to neighbor address
                
                print(f"Sending DV to node {neighbor_node}")                            # IMP: send message
                dv_message = f"{node}:{DV[node_index]}"                                 # if 'A' send A:{0, 2, 0, 0, 1}
                client_socket.sendall(dv_message.encode())
                client_socket.close()
            except Exception:
                print(f"Failed to send DV from {node} to {neighbor_node}")


def receive_dv_messages(node):
    node_index = nodes.index(node)
    
    N = len(DV[node_index])                                                         # Lenght of the DV row
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)               # Create a socket
    node_port = ports[node]                                                         # Assign the port 
    node_address = ('localhost',node_port)                                          # Get the port of the node
    server_socket.bind(node_address)                                                # Bind/Connect to the node 
    server_socket.listen(N)                                                         # Create a listener to listen for N times

    while True:
        conn, addr = server_socket.accept()

        port_no = addr[1]                                                           # addr = (ip_address, port_no)
        for client_node, client_port in ports.items():                              # ports = {'A': 8000, ...}
            if client_port == port_no:
                print(f"Node {node} received DV from {client_node}")


        data = conn.recv(1024).decode()
        client_node, client_dv = data.split(":")
        print(f"Updating DV at Node {node}")
        calc_DV(node, client_node, client_dv)
       

def calc_DV(node, client_node, client_DV):
    # given we are in Node A, we DV info from Node B
    # Old node:            {0 2 0 0 1}
    # client node:         {2 0 5 0 0}
    # New node:            {0 2 7 0 1}
    # Recalculate distance vector (DV) based on received DV from neighboring nodes
    node_index = nodes.index(node)
    client_index = nodes.index(client_node)
    client_offset = DV[node_index][client_index]

    line_len = len(DV[node_index])
    for index in range(line_len):
        client_dv = client_DV[index]                                                # client_dv = DV[index]
        if index != node_index and client_dv != 0:                                  # if not self
            DV[node_index][index] += client_DV[index] +  client_offset              # To update the distance vector


def receive_DV(node):
    # Receive distance vector (DV) from neighboring nodes
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', ports[node]))
    sock.listen(5)
    while not stop_flag:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        
        sender, received_DV = data.split(':')                                      # A : 0
        received_DV = eval(received_DV)
        conn.close()
        if update_DV(sender, received_DV):
            print(f"Node {node} received DV from {sender}")
            print(f"Updating DV at node {node}")
            print(f"New DV at node {node} = {DV[node]}")
            send_DV(node)  # Broadcast updated DV to neighboring nodes

def eval_DV(node, new_DV):
    # Update distance vector (DV) with new information given                        # if 'A' received A:{0, 2, 0, 0, 1}
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