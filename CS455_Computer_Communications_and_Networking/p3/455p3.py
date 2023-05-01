# Jed Mendoza G00846927
import select
import socket
import threading
import time

MAX = 10000                                                                 # any value equal or greater is invalid

# Global variables
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}
addresses = []
threads = []
DV = {}  # Distance vector table
LOCALHOST = '127.0.0.1'
N = 0

lock = threading.Lock()
output_lock = threading.Lock()
round_counter = 1                                                           # round 1 to N
turn_order = 0                                                              # whose turn to send messages
output = open("output.txt", "a+")                                           # with output as f


def network_init():
    global DV, N, addresses, threads
    _ = open("output.txt", "w")                                                        # reset output

    # Read and parse txt file to initialize distance vector table (DV)
    # and set initial distances between nodes
    with open('network.txt', 'r') as file:
        node_index = 0                                                                  # node is a counter for the position of the node
        for line in file:                                                               # for each line in file
            DV[node_index] = [int(x) for x in line.split(" ")]                          # "0 2 0 0 1" -> [0, 2, 0, 0, 1]
            N = len(DV[node_index])                                                     # length of the DV

            for edge in range(N):                                                       # access each individual element in line
                if DV[node_index][edge] == 0 and edge != node_index:
                    DV[node_index][edge] = MAX                                          # if there is no immediate connection, set to MAX int

            # Create and start thread for sending, receiving messages
            server_node = nodes[node_index]                                             # node = 'A' or 'B' or ... or 'E'
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (LOCALHOST, ports[server_node])
            server_socket.bind(server_address)
            print(f"Node {server_node} is listening")
            server_socket.listen(N)
            server_socket.settimeout(0.5)
            
            # setup select
            print(f"Blocking set to false in Node {server_node}")
            server_socket.setblocking(0)                                                # allows multiple socket access
            addresses.append(server_address)

            # create threads
            print(f"Creating thread for Node {server_node}")
            server_thread = threading.Thread(target=server_behavior, args=(server_socket, server_node))
            threads.append(server_thread)

            # add a new node for each new line
            node_index += 1                              

        # start  and wait for all threads
        for t in threads:
            t.start()
        for t in threads:
            t.join()


def server_behavior(server_socket, server_node):
    global round_counter, turn_order, addresses, threads
    client_sockets = []                                                                     # client sockets to connect over TCP

    try:
        curr_dv = DV[nodes.index(server_node)]
        last_dv = curr_dv

        input_data = []                                                                     # server reads these messages
        output_addresses = []                                                               # server writes to these addresses 
        while round_counter < N:
            if nodes.index(server_node) == turn_order:                                      # if its my turn to send
                output_addresses = get_neighbors(server_node)
                with output_lock:       
                    print(f"Round {round_counter}: {server_node}", file= output)
                    print(f"Current DV = {curr_dv}", file= output)
                    print(f"Last DV = {last_dv}", file= output)
            else:                                                                           # else its my turn to listen
                try:
                    client_socket, client_address = server_socket.accept()

                    if client_socket:
                        data = client_socket.recv(1024)
                        print(f"Node {server_node} received {data}")
                        input_data.append(data)

                        if client_sockets.count(client_socket) == 0:
                            client_sockets.append(client_socket)
                except Exception as e:
                    print(f"Error accepting in server from Node {server_node}: {e}")
                    time.sleep(0.5)                  
                    pass

            readable, writable, exceptional = select.select(input_data, output_addresses, [], 0.1)
            
            if nodes.index(server_node) == turn_order:
                for client_address in writable: 
                    print(f"Node {server_node} is sending to {client_address}")
                    send_dv_messages(server_socket, client_address)                             # send a message, then increment next
                    output_addresses.remove(client_address)

                turn_order += 1
                if server_node == nodes[-1]:                                                    # reset turn order when we get to the final node
                    round_counter += 1
                    turn_order = 0   
                    with output_lock:    
                        print("-------------------------------------------------", file= output)
            
            for data in readable:
                last_dv = curr_dv
                recv_dv_messages(server_node, data)
                input_data.remove(data)

            for something in exceptional:
                print(f"Error: {something} in Node {server_node}")
                input_data.clear()
                output_addresses.clear()    
                break

    finally:
        for each in client_sockets:
            each.close()
        server_socket.close()                                                                   # end server_behavior


def send_dv_messages(send_socket, recv_address):                                 
    send_node = nodes[addresses.index(send_socket)]
    recv_node = nodes[addresses.index(recv_address)]
    print(f"Node {send_node} sending to Node {recv_node}, address {recv_address}")
    try:
        send_socket.connect(recv_address)
        with output_lock:
            print(f"Sending DV to Node {recv_node} w/ {recv_address[1]}", file= output)
        dv_message = f"{send_node}:{DV[addresses.index(send_socket)]}"                      # if 'A' send A:{0, 2, 0, 0, 1}
        send_socket.send(dv_message.encode())
    except Exception as e:
        print(f"Error sending message from Node {send_node} to Node {recv_node}: {e}")                            
        pass                                                                                # end send_dv_messages


def recv_dv_messages(server_node, data):
    try:
        server_dv = DV[nodes.index(server_node)]
        client_node, client_dv = data.split(':')

        client_dv = [int(x) for x in client_dv[1:-1].split(",")]
        with output_lock:
            print(f"Node {server_node} received DV from {client_node}", file= output)
            print(f"Updating DV at Node {server_node}", file= output)

        calc_DV(server_node, client_node, client_dv)                                    # check the received data
        with output_lock:
            if DV[nodes.index(server_node)] != server_dv:                               # if the dv is updated  
                print(f"New DV at Node {server_node} = {DV[nodes.index(server_node)]}", file= output)
            else:                                                                       # was not updated
                print(f"No change in DV at Node {server_node}", file= output)
    except Exception as e:
        print(f"Error receiving message in Node {server_node} from Node {client_node}: {e}")                            
        pass                                                                                # end recv_dv_messages
        

def calc_DV(server_node, client_node, client_DV):
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


def get_neighbors(server_node):
    neighbors = []
    server_dv = DV[nodes.index(server_node)]
    
    index = 0
    for neighbor in server_dv:
        if neighbor != 0 and neighbor < MAX:
            print(f"Node {server_node} and my neighbor is {addresses[index]}")
            neighbors.append(addresses[index])
        index += 1  

    return neighbors


def main():
    try:
        network_init()
        print(f"Routing algorithm stopped", file= output)

    finally:
        output.close()
        
if __name__ == "__main__":
    main()