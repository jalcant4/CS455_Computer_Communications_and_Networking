## Jed Alcantara G00846927


## import (add more as you need)
import struct
import threading
import unreliable_channel
import numpy as np
import zlib
from Timer import Timer
import time
import socket
import sys

# constants
UDP_HEADER_SIZE = 28
MTP_HEADER_SIZE = 16
MAX_DATA_SIZE = 1500 - UDP_HEADER_SIZE - MTP_HEADER_SIZE
TIMEOUT = 0.5

## define and initialize
# rec_window_size, rec_window_base, seq_number, dup_ack_count, etc.
receiver_ip = "127.0.0.1"
receiver_port = None
output = None
receiver_log = None
receiver_socket = None
sender_addr = None

data_type = None
seq_num = 0
data_length = MAX_DATA_SIZE
checksum = 0
data = None

received_data = []
expected_seq_number = 0

timer = None

lock = threading.Lock()

def int_to_bytes(i):
    return i.to_bytes(4, byteorder='big')

def bytes_to_int(b):
    return int.from_bytes(b, byteorder='big')

# assumption: values except data are bytes
def calc_checksum(data_type, seq_num, data_length, data):
    checksum = 0
    
    # Convert bytes to bytearray or bytes-like object
    data_type_bytes = bytearray(data_type)
    seq_num_bytes = bytearray(seq_num)
    data_length_bytes = bytearray(data_length)
    
    # Calculate checksum incrementally in chunks
    CHUNK_SIZE = 1024  # adjust chunk size as needed
    data_in_bytes = data.encode()
    for i in range(0, len(data_in_bytes), CHUNK_SIZE):
        chunk = data_in_bytes[i:i+CHUNK_SIZE]
        checksum = zlib.crc32(data_type_bytes + seq_num_bytes + data_length_bytes + chunk, checksum)

    return checksum.to_bytes(4, byteorder='big')



# MTP ACK packet will have the same fields in its header, without any data.
# assumption: must call extract_data_packet, otherwise behavior is undefined
def create_ack_packet(seq_num):
    # create ack packet
    # crc32 available through zlib library
    packet_type = bytes(b'ACK')
    packet_format = '!4s4s4s4s'
    
    packet_format = '!4s4s4s4s'
    packet = struct.pack(packet_format, packet_type, seq_num, data_length, checksum)
    return packet


def extract_data_packet(packet):
    global data_type, seq_num, data_length, checksum, data
    
    # Extract the MTP header from the packet
    mtp_header = packet[:MTP_HEADER_SIZE]
    
    # Unpack the values from the MTP header using the struct format
    data_type, seq_num, data_length, checksum = struct.unpack('!4s4s4s4s', mtp_header)
    
    # Extract the data from the packet and decode it as UTF-8
    data = packet[MTP_HEADER_SIZE:].decode('utf-8')


# assumption: must call extract_data_packet, otherwise behavior is undefined
def validate_packet(packet):
    extract_data_packet(packet)
    calculated_checksum = calc_checksum(data_type, seq_num, data_length, data)

    if (bytes_to_int(seq_num) != expected_seq_number):
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = OUT OF ORDER PACKET".format(
        data_type, seq_num, data_length, checksum, calculated_checksum), file=receiver_log) 
    elif (checksum != calculated_checksum):
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = CORRUPT".format(
        data_type, seq_num, data_length, checksum, calculated_checksum), file=receiver_log)
    else:
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = NOT CORRUPT".format(
        data_type, seq_num, data_length, checksum, calculated_checksum), file=receiver_log)  
    
    return checksum == calculated_checksum and bytes_to_int(seq_num) == expected_seq_number

def send_ack(seq_num, sender_addr):
    # TODO print
    # create ack packet with seq_num and send to sender
    ack_packet = create_ack_packet(seq_num)
    unreliable_channel.send_packet(receiver_socket, ack_packet, sender_addr)

# receives packets from the sender
def receive_thread(receiver_socket):
    global received_data, expected_seq_number, timer, sender_addr

    while True:
        # send ack packets but using unreliable channel
        packet, sender_addr = unreliable_channel.recv_packet(receiver_socket)

        #start the timer
        if timer is None:
            timer = Timer(TIMEOUT)
            timer.start()
        
        # checks for next packet
        while timer.is_running() and not timer.timeout():
            with lock:
                # Arrival of an in-order packet with expected sequence #
                if validate_packet(packet):
                    received_data.append(data)
                    output.write(data)

                    expected_seq_number += 1
                    send_ack(seq_num, sender_addr) 
                    break
                # Arrival of an out-of-order packet with higher-than-expected sequence 
                #   or the arrival of a packet that is corrupt
                else:
                    if expected_seq_number > 0: 
                        send_ack (expected_seq_number - 1, sender_addr)
                    else: send_ack (expected_seq_number, sender_addr)
            time.sleep(0.1)
        
        # timed out, resend last ack
        if timer.timeout():
            send_ack (expected_seq_number - 1, sender_addr)
        
        timer = None
        
def main():
    global receiver_ip, receiver_port, output, receiver_log, receiver_socket

	# read the command line arguments
    receiver_port = int(sys.argv[1])
    # open log file and start logging
    output = open(sys.argv[2], 'w+')
    receiver_log = open(sys.argv[3],'w+')

    # open UDP socket
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # print("Connecting......")
    server_address = (receiver_ip, receiver_port)
    receiver_socket.bind(server_address)

    rcv_thread = threading.Thread(target=receive_thread, args=(receiver_socket,))
    rcv_thread.start()    

# your main thread can act as the receive thread that receives DATA packets
main()


