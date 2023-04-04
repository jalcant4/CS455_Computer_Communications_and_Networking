## Jed Alcantara G00846927


## import (add more as you need)
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

## define and initialize
# rec_window_size, rec_window_base, seq_number, dup_ack_count, etc.
receiver_ip = "127.0.0.1"
receiver_port = None
output = None
receiver_log = None
receiver_socket = None
sender_addr = None

received_data = []

data_type = None
seq_num = 0
data_length = MAX_DATA_SIZE
checksum = 0
data = None

expected_seq_number = 0

timer = None
ack_timeout = 1

lock = threading.Lock()

def int_to_bytes(i):
	return np.int64(i).tobytes()

def bytes_to_int(b):
	return np.frombuffer(b, dtype=np.uint32)[0]

def calc_checksum(type_data, seq_num, data_length, data):
    checksum = 0

    type_data = int_to_bytes(type_data)
    seq_num = int_to_bytes(seq_num)
    data_length = int_to_bytes(data_length)
    data = int_to_bytes(data)

    checksum = zlib.crc32(type_data + seq_num + data_length + data)
    return int_to_bytes(checksum)

# MTP ACK packet will have the same fields in its header, without any data.
# assumption: must call extract_packet, otherwise behavior is undefined
def create_ack_packet(seq_num):
    # create ack packet
    # crc32 available through zlib library
    packet_type = b'ACK'
    seq_num = int_to_bytes(seq_num)
    data_length = int_to_bytes(len(data))
    checksum = calc_checksum(type_data, seq_num, data_length, data)
    
    ack_packet = packet_type + seq_num + data_length + checksum
    return ack_packet

def extract_packet(packet):
    global type_data, seq_num, data_length, checksum, data
    
    # extract the data after receiving
    mtp_header = packet[UDP_HEADER_SIZE:UDP_HEADER_SIZE + MTP_HEADER_SIZE]
    type_data = bytes_to_int(mtp_header[0:4])
    seq_num = bytes_to_int(mtp_header[4:8])
    data_length = bytes_to_int(mtp_header[8:12])
    checksum = bytes_to_int(mtp_header[12:16])
    data = packet[MTP_HEADER_SIZE:].decode('utf-8')

# assumption: must call extract_packet, otherwise behavior is undefined
def validate_packet():
    calculated_checksum = calc_checksum(type_data, seq_num, data_length, data)

    if (seq_num != expected_seq_number):
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = OUT OF ORDER PACKET".format(
        type_data, seq_num, data_length, checksum, calculated_checksum), file=receiver_log) 
    elif (checksum != calculated_checksum):
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = CORRUPT".format(
        type_data, seq_num, data_length, checksum, calculated_checksum), file=receiver_log)
    else:
        print("Packet_received: type= {}; seqNum = {}; length = {}; checksum_in_packet = {}; calculated_checksum = {}; status = NOT CORRUPT".format(
        type_data, seq_num, data_length, checksum, calculated_checksum), file=receiver_log)  
    
    return checksum == calculated_checksum and seq_num == expected_seq_number

def send_ack(seq_num, sender_addr):
    # create ack packet with seq_num and send to sender
    ack_packet = create_ack_packet(seq_num)
    receiver_socket.sendto(ack_packet, sender_addr)

# receives packets from the sender
def receive_thread(receiver_socket):
    global received_data, expected_seq_number, timer,sender_addr

    while True:
        # send ack packets but using unreliable channel
        packet, sender_addr = unreliable_channel.recv_packet(receiver_socket)
        extract_packet(packet)

        if data == '' or data is None: 
            break

		#log recieved file on file
        receiver_log.write("Packet recieved; {} \n".format(validate_header(packet_from_server, calc_checksum(type_data, seqNum, data_length))))

		#check for corrupted data
        if checksum != bytes_to_int(calc_checksum(type_data, seqNum, data_length)):
            receiver_log.write("Corrupted data while receiving packet with seqNum: {} \n".format(seqNum))
		# done with receiving packets
        else : 
            receiver_log.write("Packets received with seqNum: {} \n".format(seqNum))

            if seqNum > expected_seq_num:
                receiver_log.write("Package with seqNum: {} out of order while expecting seq: {} Sending dup ack with seqNum : {}. \n".format(seqNum, expected_seq_num, expected_seq_num))
                send_ack()
            else: 
                expected_seq_num = seqNum + 1
                out_txt.write(data)
                if ack_timeout_timer is not None and ack_timeout_timer.is_alive() : 
					# was waiting for second packet and got it 
                    ack_timeout_timer.cancel()
                    send_ack()
                else :
                    ack_timeout_timer = threading.Timer(500, send_ack)
                    ack_timeout_timer.start()
    return data


def main():
    # Some of the things to do:
    # open log file and start logging
	# read the command line arguments
	# open UDP socket
    receiver_ip = sys.argv[1]
    receiver_port = int(sys.argv[2])
    out_txt = sys.argv[3]
    receiver_log = sys.argv[4]
    
    receiver_log = open(receiver_log,'w+')
    out_txt = open(out_txt, 'w+')
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Establishing Connection........")
    
    receiver_socket.bind(receiver_ip,receiver_port)
    
    #start the timer
    if timer is None:
        timer = Timer(ack_timeout, send_ack, args=(expected_seq_number, sender_addr))
        timer.start()
        
        #checks for next packet
        while not timer.timeout():
            with lock:
                # Arrival of an in-order packet with expected sequence #
                if validate_packet():
                    received_data.append(data)
                    print(data, f=output)

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

    receive_thread = threading.Thread(target=receive_thread, args=(receiver_socket,))
    receive_thread.start()    

# your main thread can act as the receive thread that receives DATA packets
main()


