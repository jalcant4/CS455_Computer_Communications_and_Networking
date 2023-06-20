# Jed Mendoza G00846927
# Amit Khadka G01245732
    
import socket
import threading
import time
import errno

MAX = 10000                                                                 # any value equal or greater is invalid

# Global variables
nodes = ['A', 'B', 'C', 'D', 'E']
ports = {'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004, 'E': 8005}
DV = {}  # Distance vector table
N = 0
FINAL_NODE = None

lock = threading.Lock()

round_counter = 1                                                           # round counter 0 to N
                                                                            # round 0 init, round 1 to N node_behavior
turn_order = 0                                                              # whose turn to send messages

output = open("output.txt", "w+")

def network_init():
    global DV, N, FINAL_NODE
    threads = []
    # Read and parse txt file to initialize distance vector table (DV)
    # and set initial distances between nodes
    with open('network.txt', 'r') as file:
        node_index = 0                                                                  # node is a counter for the position of the node
        for line in file:                                                               # for each line in file
            DV[node_index] = [int(x) for x in line.split(" ")]                          # "0 2 0 0 1" -> [0, 2, 0, 0, 1]
            N = len(DV[node_index])                                                     # length of the DV
            FINAL_NODE = nodes[N - 1]                                                   # last node in DV

            for edge in range(N):                                                       # access each individual element in line
                if DV[node_index][edge] == 0 and edge != node_index:
                    DV[node_index][edge] = MAX                                          # if there is no immediate connection, set to MAX int

            # Create and start thread for sending, receiving messages
            server_node = nodes[node_index]                                             # node = 'A' or 'B' or ... or 'E'
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind(('localhost', ports[server_node]))
            server_socket.setblocking(False)

            server_thread = threading.Thread(target=server_behavior, args=(server_node, server_socket))
            server_thread.start()
            threads.append(server_thread)

            # add a new node for each new line
            node_index += 1                              

        # wait for all threads to end
        for t in threads:
            t.join()


def server_behavior(server_node, server_socket):
    global round_counter, turn_order
    try:
        while round_counter < N:
            if nodes.index(server_node) == turn_order:                                      # if is my turn; then send messages            
                print(f"Round {round_counter}: {server_node}", file= output)
                print(f"Current DV = {DV[nodes.index(server_node)]}", file= output)
                print(f"Last DV = {DV[nodes.index(server_node)]}", file= output)                             
                send_dv_messages(server_socket, server_node)                                # send a message
                
                turn_order += 1
                if server_node == FINAL_NODE:
                    round_counter += 1
                    turn_order = 0
            try:
                server_socket.setblocking(False)##
                data = server_socket.recv(1048)##
                server_socket.setblocking(True)##
                if data:
                    recv_dv_messages(server_node, data.decode())
            except BlockingIOError:
                continue
            except ConnectionResetError:
                print("Connection Reser byt peer", file= output)
                server_socket.close()
                break
    except ConnectionResetError:
        print("Connection Reser by peer", file= output)
    server_socket.close()



def send_dv_messages(send_socket, send_node):                                       
    for recv_node in nodes:
        send_index = nodes.index(send_node)
        recv_index = nodes.index(recv_node)
        if recv_node != send_node and DV[send_index][recv_index] < MAX:
            try:
                receiver_node = nodes[recv_index]                                       # define receiver node  
                receiver_address = ('localhost', ports[receiver_node])                  # define receiver address
                
                print(f"Sending DV to node {receiver_node}", file= output)                            # IMP: send message
                dv_message = f"{send_node}:{DV[send_index]}"                            # if 'A' send A:{0, 2, 0, 0, 1}
                send_socket.sendto(dv_message.encode(), receiver_address)
                time.sleep(0.5)                                                         # allow receiver thread to update
                
            except ConnectionError:
                print(f"Connection error while sending message to Node {receiver_node}", file= output)
            except TimeoutError:
                print(f"Timeout error while sending message to Node {receiver_node}", file= output)
            except Exception as e:
                print(f"Error sending message to Node {receiver_node}: {e}", file= output)
                break


def recv_dv_messages(server_node, data):
    server_dv = DV[nodes.index(server_node)]                                            # get the dv of the receiver node
    print(f"Server node inside recv_dv_messages: {server_dv}", file= output)
    try:
        client_node, client_dv = data.split(':')
        client_dv = [int(x) for x in client_dv[1:-1].split(",")]
        print(f"Updating DV at Node {server_node}", file= output)                                     # check the received data

        calc_DV(server_node, client_node, client_dv)

        if DV[nodes.index(server_node)] != server_dv:                                   # if the dv is updated notify    
            print(f"New DV at Node {server_node} = {DV[nodes.index(server_node)]}", file= output)
        else:
            print(f"No change in DV at Node {server_node}\n\n", file= output)
    except BlockingIOError:                                                             # no incoming messages
        print(f"BlockingIOError in Node {server_node}", file= output)
        pass
    except:                                                                             # other error
        pass
        

# def calc_DV(server_node, client_node, client_DV):
#     global DV
#     # given we are in Node A, we DV info from Node B
#     # Old node:            {0 2 0 0 1}
#     # client node:         {2 0 5 0 0}
#     # New node:            {0 2 7 0 1}
#     # Recalculate distance vector (DV) based on received DV from neighboring nodes
#     server_index = nodes.index(server_node)                                    # a reference to self
#     server_DV = DV[server_index]                                                
#     dv_len = len(DV[server_index])
    
#     print(f"CALCULATING THE DV YOYOYOYYOYO")

#     client_index = nodes.index(client_node)
#     client_offset = server_DV[client_index]
#     print(f"client index = {client_index} and Client offset = {client_offset} and dv length = {dv_len} , server index = {server_index}")
#     with lock:
#         for index in range(dv_len):
#             print("Got it this far***************************")
#             if index != server_index:                                              # if self dont update at server_index
#                 continue
#             elif server_index >= client_index + client_offset: 
#                 print("**********I am here inside elif of cal_dv-------")                                                  
#                 server_DV[index] = client_DV[index] +  client_offset              # To update the distance vector
    
def calc_DV(server_node, client_node, client_DV):
    global DV
    server_index = nodes.index(server_node)
    server_DV = DV[server_index]
    dv_len = len(server_DV)
    client_index = nodes.index(client_node)
    client_offset = server_DV[client_index]
    with lock:
        for index in range(dv_len):
            if index == server_index:
                continue
            elif server_DV[index] > client_DV[index] + client_offset:
                server_DV[index] = client_DV[index] + client_offset
    DV[server_index] = server_DV



def main():
    try:
        network_init()
        print("Routing algorithm stopped", file= output)
    finally:
        output.close()


main()