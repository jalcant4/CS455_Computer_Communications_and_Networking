# Jed Mendoza G00846927
    
import socket
import threading
import select

MAX = 10000                                                                 # any value equal or greater is invalid

# Global variables
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}
sockets = []
DV = {}  # Distance vector table
N = 0

lock = threading.Lock()
round_counter = 1                                                           # round 1 to N
turn_order = 0                                                              # whose turn to send messages
output = open("output.txt", "a+")                                           # with output as f


def network_init():
    global DV, N, sockets
    threads = []
    _ = open("output.txt", "w+")                                                        # reset output

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
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind(('localhost', ports[server_node]))
            server_socket.settimeout(0.5)
            
            # setup select
            server_socket.setblocking(0)                                                # allows multiple socket access
            sockets.append(server_socket)

            # create threads
            server_thread = threading.Thread(target=server_behavior, args=(server_socket,))
            threads.append(server_thread)

            # add a new node for each new line
            node_index += 1                              

        # start  and wait for all threads
        for t in threads:
            t.start()
        for t in threads:
            t.join()


def server_behavior(server_socket):
    global round_counter, turn_order, sockets

    server_node = nodes[sockets.index(server_socket)]
    curr_dv = DV[nodes.index(server_node)]
    last_dv = curr_dv

    input_data = []                                                                         # server expects messages from these
    output_sockets = []                                                                     # server writes to these sockets 


    while round_counter < N:
        if sockets.index(server_socket) == turn_order:                                      # if my turn, fill output_sockets
            output_sockets = get_neighbors(server_node)
            with lock:
                with output as f:          
                    print(f"Round {round_counter}: {server_node}", file= f)
                    print(f"Current DV = {curr_dv}", file= f)
                    print(f"Last DV = {last_dv}", file= f)

        try:
            data, _ = server_socket.recv(1024)
            if data:
                input_data.append(data)
        except BlockingIOError:
            pass
        
        readable, writable, exceptional = select.select(input_data, output_sockets, [], 0.5)
        
        if len(writable) > 0:
            for client_socket in writable: 
                with lock:
                    send_dv_messages(server_socket, client_socket)                          # send a message, then increment next
                output_sockets.remove(client_socket)
            
            turn_order += 1
            if server_node == nodes[-1]:                                                    # reset turn order when we get to the final node
                round_counter += 1
                turn_order = 0       
                with output as f:  
                    print("-------------------------------------------------", file= f)
        
        for data in readable:
            last_dv = curr_dv
            recv_dv_messages(server_socket, client_socket)
            input_data.remove(data)

        for something in exceptional:
            print(f"Error: {something} in Node {server_node}")
            input_data.clear()
            output_sockets.clear()    
            break


def send_dv_messages(send_socket, recv_socket):                                 
    send_node = nodes[sockets.index(send_socket)]
    recv_node = nodes[sockets.index(recv_socket)]
    try:
        receiver_address = ('localhost', ports[recv_node])                                  # define receiver address
        with output as f:
            print(f"Sending DV to node {recv_node}", file= f)                               # IMP: send message
        dv_message = f"{send_node}:{DV[sockets.index(send_socket)]}"                        # if 'A' send A:{0, 2, 0, 0, 1}
        send_socket.sendto(dv_message.encode(), receiver_address)

    except ConnectionError:
        print(f"Connection error while sending message to Node {recv_node}")
        pass
    except TimeoutError:
        print(f"Timeout error while sending message to Node {recv_node}")
        pass
    except Exception as e:
        print(f"Error sending message to Node {recv_node}: {e}")                            
        pass                                                                                # end send_dv_messages

def recv_dv_messages(server_socket, data):
    try:
        server_node = nodes[sockets.index(server_socket)]
        server_dv = DV[nodes.index(server_node)]
        client_node, client_dv = data.split(':')
        client_dv = [int(x) for x in client_dv[1:-1].split(",")]

        with output as f:                                                                   # print that you received data
            print(f"Node {server_node} received DV from {client_node}", file= f)
            print(f"Updating DV at Node {server_node}", file= f)

        calc_DV(server_node, client_node, client_dv)                                        # check the received data
        with output as f:
            if DV[nodes.index(server_node)] != server_dv:                                   # if the dv is updated  
                print(f"New DV at Node {server_node} = {DV[nodes.index(server_node)]}", file= f)
            else:                                                                           # was not updated
                print(f"No change in DV at Node {server_node}", file= f)

    except BlockingIOError:                                                                 # no incoming messages
        print(f"BlockingIOError in Node {server_node}")
        pass
    except:                                                                                 # other error
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
            neighbors.append(sockets[index])
        index += 1  

    return neighbors


def main():
    try:
        network_init()
        with output as f:
            print(f"Routing algorithm stopped", file= f)
    finally:
        for socket in sockets:
            socket.close()
        output.close()
        
if __name__ == "__main__":
    main()