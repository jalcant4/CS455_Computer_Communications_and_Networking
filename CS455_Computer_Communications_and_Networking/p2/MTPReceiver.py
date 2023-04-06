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
FINAL_SEQ_NUM = 2 ** 31

## define and initialize
# rec_window_size, rec_window_base, seq_number, dup_ack_count, etc.
receiver_ip = '127.0.0.0'
receiver_port = None
output = None
receiver_log = None
receiver_socket = None
sender_addr = None

received_data = []
expected_seq_number = 0

# receiver packet info are in bytes
ack_seq_num = 0
ack_length = 0
ack_checksum = 0

timer = None

lock = threading.Lock()


def int_to_bytes(i):
    return i.to_bytes(4, byteorder='big')


def bytes_to_int(b):
    return int.from_bytes(b, byteorder='big')


def calc_checksum(data_type, seq_num, data_length, data):
    checksum = 0
    
    # Calculate checksum incrementally in chunks
    CHUNK_SIZE = MAX_DATA_SIZE  # adjust chunk size as needed
    data_in_bytes = data.encode('utf-8')
    for i in range(0, len(data_in_bytes), CHUNK_SIZE):
        chunk = data_in_bytes[i:i+CHUNK_SIZE]
        checksum = zlib.crc32(data_type + seq_num + data_length + chunk, checksum)

    return checksum.to_bytes(4, byteorder='big')



# MTP ACK packet will have the same fields in its header, without any data.
# assumption: must call extract_data_packet, otherwise behavior is undefined
def create_ack_packet(packet_type, seq_num, packet_length, checksum):
    global ack_seq_num, ack_length

    ack_seq_num = int_to_bytes(seq_num)
    ack_length = int_to_bytes(packet_length)
    
    packet_format = '!4s4s4s4s'
    packet = struct.pack(packet_format, packet_type, ack_seq_num, ack_length, checksum)
    return packet


def extract_data_packet(packet):
    # Extract the MTP header from the packet
    mtp_header = packet[:MTP_HEADER_SIZE]
    
    # Unpack the values from the MTP header using the struct format
    data_type, seq_num, data_length, checksum = struct.unpack("!4s4s4s4s", mtp_header)

    # Convert the bytes objects to integer values
    data_type = data_type.decode('utf-8')
    data_seq_num = bytes_to_int(seq_num)
    data_length = bytes_to_int(data_length)
    data_checksum = checksum.hex()
    # Extract the data from the packet and decode it as UTF-8
    data = packet[MTP_HEADER_SIZE:].decode('utf-8')

    return data_type, data_seq_num, data_length, data_checksum, data


def validate(data_type, data_seq_num, data_length, data_checksum, ack_checksum):

    if data_seq_num != expected_seq_number:
        status = "OUT OF ORDER PACKET"
    elif data_checksum != ack_checksum:
        status = "CORRUPT"
    else:
        status = "NOT CORRUPT"

    receiver_log.write("Packet_received: type={}; seqNum={}; length={}; checksum_in_packet={}; calculated_checksum={}; status={}\n".format(
         data_type, data_seq_num, data_length, data_checksum, ack_checksum, status
    ))

    return data_checksum == ack_checksum and data_seq_num == expected_seq_number


def send_ack(ack_packet, sender_addr):
    unreliable_channel.send_packet(receiver_socket, ack_packet, sender_addr)
    
    type, num, length, checksum, _ = extract_data_packet(ack_packet)

    receiver_log.write("Packet sent; type={}; seqNum{}; length={}; checksum_in_packet={};\n".format(
        type, num, length, checksum
    ))


# receives packets from the sender
def receive_thread(receiver_socket):
    global received_data, expected_seq_number, timer, sender_addr

    while True:
        # receive packets but using unreliable channel
        data_packet, sender_addr = unreliable_channel.recv_packet(receiver_socket)
        data_type, data_seq_num, data_length, data_checksum, data = extract_data_packet(data_packet)

        if data_seq_num == FINAL_SEQ_NUM:
             break
        
        # start the timer
        ack_checksum = calc_checksum(data_type.encode('utf-8'), int_to_bytes(data_seq_num), int_to_bytes(data_length), data)
        in_sequence_and_checksum = validate(data_type, data_seq_num, data_length, data_checksum, ack_checksum.hex())
        # Arrival of an in-order packet with expected sequence #
        if in_sequence_and_checksum:
            timer = Timer(TIMEOUT, handle_timeout)

            with lock:
                expected_seq_number += 1

            if received_data.count(data) == 0:
                received_data.append(data)
                output.write(data)

            # create ack packet with seq_num and send to sender
            ack_packet = create_ack_packet(b'_ACK', data_seq_num, MTP_HEADER_SIZE, ack_checksum)
            send_ack(ack_packet, sender_addr)
            timer.start()
        # Arrival of an out-of-order packet with higher-than-expected sequence 
        #   or the arrival of a packet that is corrupt
        else:
            if len(received_data) > 0:
                data_type, seq_num, length, checksum, data = extract_data_packet(received_data[len(received_data) - 1])
                timer = Timer(TIMEOUT, handle_timeout)

                ack_packet = create_ack_packet(b'ACK', seq_num, MTP_HEADER_SIZE, bytes.fromhex(checksum))
                send_ack(ack_packet, sender_addr)    
                timer.start()
            
        time.sleep(0.01)
    
    receiver_socket.close()
 

# handlers
def handle_timeout():
    global timer
    if len(received_data) > 0:
        data_type, seq_num, length, checksum, data = extract_data_packet(received_data[len(received_data) - 1])
        
        timer = Timer(TIMEOUT, handle_timeout)

        ack_packet = create_ack_packet(b'ACK', seq_num, MTP_HEADER_SIZE, bytes.fromhex(checksum))
        send_ack(ack_packet, sender_addr)    
        timer.start()


def main():
    global receiver_ip, receiver_port, output, receiver_log, receiver_socket

    try:
        # read the command line arguments
        receiver_port = int(sys.argv[1])
        # open log file and start logging
        output = open(sys.argv[2], 'w+')
        receiver_log = open(sys.argv[3],'w+')

        # open UDP socket
        receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver_log.write("MTP Receiver is connecting .\n")
        time.sleep(0.5)
        receiver_log.write("MTP Receiver is connecting ..\n")
        time.sleep(0.5)
        receiver_log.write("MTP Receiver is connecting ...\n")
        receiver_address = (receiver_ip, receiver_port)
        receiver_socket.bind(receiver_address)

        rcv_thread = threading.Thread(target=receive_thread, args=[receiver_socket])
        rcv_thread.start()
        rcv_thread.join()
    finally:
        receiver_socket.close()    
        receiver_log.close()
        output.close()
# your main thread can act as the receive thread that receives DATA packets
main()

