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
import sys
import threading
import signal

# Global variables
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}
DV = {}  # Distance vector table
lock = threading.Lock()
stop_flag = False  # Stop condition flag
round_counter_lock = threading.Lock()

MAX = 10000
round_counter = 1

def network_init():
    threads = []
    # Read and parse txt file to initialize distance vector table (DV)
    # and set initial distances between nodes
    with open('network.txt', 'r') as file:
        node_index = 0                                              # node is a counter for the position of the node
        for line in file:                                           # for each line in file
            DV[node_index] = [int(x) for x in line.split(" ")]      # "0 2 0 0 1" -> [0, 2, 0, 0, 1]
            dv_len = len(DV[node_index])

            for edge in range(dv_len):                              # access each individual element in line
                if DV[node_index][edge] == 0 and edge != node_index:
                    DV[node_index][edge] = MAX                      # if there is no immediate connection, set to MAX int


            # Create and start thread for sending and receiving messages
            node = nodes[node_index]                        # node = 'A' or 'B' or ... or 'E'
            #print(f"Round {round_counter} : {node}")
            #print(f"Current DV at Node {nodes[node_index]} = {DV[node_index]}")
            t_send = threading.Thread(target=send_dv_messages, args=(node,))
            t_send.start()
            threads.append(t_send)


            t_receive = threading.Thread(target=receive_dv_messages, args=(node,))
            t_receive.start()
            threads.append(t_receive)
            

            # add a new node for each new line
            node_index += 1                                


        # wait for all threads to end
        for t in threads:
            t.join()


def send_dv_messages(server_node):
    global round_counter
    server_index = nodes.index(server_node)                                             # node_index = 0 if 'A' ... 4 if 'E'
    print(f"Round {round_counter} : {server_node}")
    print(f"Current DV at Node {nodes[server_index]} = {DV[server_index]}")
    N = len(DV[server_index])                                                           # N = len ()
    #print(f"Round {round_counter} : {server_node}")
    print(f"Server index {server_index} Server node {server_node}")
    while not stop_flag:
        with lock:
            for dv_index in range(N):                                                           # iterate through each edge of the node
                print(f"dv_index : {dv_index} and N : {N}")
                if (dv_index != server_index) or (dv_index != MAX):                               # if not self
                    try:
                        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        neighbor_node = nodes[dv_index]                                         # attempt to retrieve neighbor
                        neighbor_port = ports[neighbor_node]                                    # retrieve Port No. of neighbor    
                        neighbor_address = ('localhost', neighbor_port)                         # define neighbor address

                        client_socket.connect(neighbor_address)                                 # connect to neighbor address
                        
                        dv_message = f"{server_node}:{DV[server_index]}"                        # if 'A' send A:{0, 2, 0, 0, 1}
                        print(f"Sending DV to node {neighbor_node}")                            # IMP: send message
                        
                        client_socket.sendall(dv_message.encode())
                        client_socket.close()
                    except Exception:
                        print(f"Failed to send DV from {server_node} to {neighbor_node}")
                        break
            
            if server_node =='E':
                print("----------------------HERE-----------------------------------")
                with round_counter_lock:
                    round_counter += 1
                    break

def receive_dv_messages(server_node):
    global round_counter
    server_index = nodes.index(server_node)
    
    N = len(DV[server_index])                                                       # Lenght of the DV row
    #print("-----------------INside receive_dv_messages function-----------------")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)               # Create a socket
    server_port = ports[server_node]                                                # Assign the port 
    node_address = ('localhost', server_port)                                       # Get the port of the node
    server_socket.bind(node_address)                                                # Bind/Connect to the node 
    server_socket.listen(N)                                                         # Create a listener to listen for N times
    while not stop_flag:
        #with lock:
            #with round_counter_lock:
        while True:
            print("-----------------INside receive_dv_messages function-----------------")
            conn, addr = server_socket.accept()
            print(f"Conn, addr : {conn,addr}")

            port_no = addr[1]                                                        # addr = (ip_address, port_no)
            print(f"port_no : {port_no}")
            for client_node, client_port in ports.items():                              # ports = {'A': 8000, ...}
                print(f"port items : {ports.items()}")
                #if client_port == port_no:
                print(f"Node {server_node} received DV from {client_node}")

            data = conn.recv(1024).decode()                                             # data is decoded into int
            client_dv = [int(x) for x in data[3:-1].split(",")]                         # data is always format "A:[X, Y, ...,Z]"

            print(f"Updating DV at Node {server_node}")
            old_DV = DV[server_index]
            calc_DV(server_node, client_node, client_dv)

            if DV[server_index] != old_DV:
                print(f"New DV at Node {server_node} = {DV[server_index]}")
    round_counter += 1


def calc_DV(server_node, client_node, client_DV):
    # given we are in Node A, we DV info from Node B
    # Old node:            {0 2 0 0 1}
    # client node:         {2 0 5 0 0}
    # New node:            {0 2 7 0 1}
    # Recalculate distance vector (DV) based on received DV from neighboring nodes
    server_index = nodes.index(server_node)                                    # a reference to self
    server_DV = DV[server_index]                                                
    dv_len = len(DV[server_index])

    client_index = nodes.index(client_node)
    client_offset = DV[server_index][client_index]
    with lock:
        for index in range(dv_len):
            if index != server_index:                                              # if self dont update at server_index
                continue
            elif server_DV[index] > client_DV[index] + client_offset:                                                   
                server_DV[index] = client_DV[index] +  client_offset              # To update the distance vector
                


def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)



def main():
    network_init()
    print("Routing algorithm stopped")

main()