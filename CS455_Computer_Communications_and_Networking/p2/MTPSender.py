## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import numpy as np
import threading
import unreliable_channel
import zlib
import socket
import sys
import Timer


PACKET_SIZE = 1456
# define and initialize
window_base = 0
window_size = 0
max_window_size = 0
dup_ack_count = 0
next_seq_number = 0
sender_log = None
packet_timeout = Timer(0.5)

## we will need a lock to protect against two concurrent threads
lock = threading.Lock()
mutex = threading.Lock()

def int_to_bytes(i):
	return np.int64(i).tobytes()

def bytes_to_int(b):
	return np.frombuffer(b, dtype=np.uint32)[0]

def calc_checksum(b1, b2, b3):
	checksum = 0
	if type(b1) is int:
		b1 = np.int64(b1).tobytes()
		b2 = np.int64(b2).tobytes()
		b3 = np.int64(b3).tobytes()
		checksum = zlib.crc32(b1+b2+b3)
	return int_to_bytes(checksum)

def getCurrWindowSize(totalpackets, window_size):
    return min(window_size, totalpackets - window_base + 1)

def create_packet(data, seq_num):
# create data packet
# crc32 available through zlib library
	type_data = b'data'  
	seq_num = int_to_bytes(seq_num)
	data_length = int_to_bytes(len(data) + 16)
	checksum = calc_checksum(type_data, seq_num, data_length)
	data = bytes(data, 'utf-8')
	return type_data + seq_num + data_length + checksum + data

def extract_packet_info(packet):
# extract the ack after receiving
	mtp_header = packet[0:16]
	type_data = bytes_to_int(mtp_header[0:4])
	seq_num = bytes_to_int(mtp_header[4:8])
	data_length = bytes_to_int(mtp_header[8:12])
	checksum = bytes_to_int(mtp_header[12:16])
	return type_data, seq_num, data_length, checksum


def receive_thread(s_socket):
	while True:
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption, take steps accordingly
		# update window size, timer, triple dup acks
		packet_from_server, server_addr = unreliable_channel.recv_packet(s_socket)
		type_data, next_seq_num, data_length, checksum = extract_packet_info(packet_from_server)

		if next_seq_num == 0:
			break
		validate_checksum = bytes_to_int(calc_checksum(type_data, next_seq_num, data_length))
		if checksum != validate_checksum:
			sender_log.write("Packet received; type=%s; seqNum=%d; length=%d; checksum_in_packet=%s; checksum_calculated=%s; status=CORUPT;",type_data, next_seq_num, data_length, checksum, validate_checksum)
		elif checksum == validate_checksum:
			if window_base == next_seq_num:
				dup_ack_count += 1
				if dup_ack_count == 3:
					mutex.acquire()
					next_seq_num = window_base
					dup_ack_count = 0
					sender_log.write("Triple Dup ACK detect")
					mutex.release()
			if window_base < next_seq_num:
				mutex.acquire()
				sender_log.write("")
				window_base = next_seq_num
				#TODO timeout
				if packet_timeout is not None:
					packet_timeout.stop()
				mutex.release()
					
     

     

#elif window_base < next_seq_num:
       	
def decode_header(packet):
    type_data, seq_num, data_length, checksum = extract_packet_info(packet)
    return "type_data= {}; seqNum = {}; data_length = {}; checksum = {}".format(
        type_data, seq_num, data_length, hex(checksum)[2:]
    )
    

def main():
	# some of the things to do:
    # open log file and start logging
    # read the command line arguments
	# open UDP socket
	reciever_ip = sys.argv[1]
	reciever_port = sys.argv[2]
	read_log_name = sys.argv[4]
	sender_log_name = sys.argv[5]
 
	# open log file and start logging
	sender_log = open(sender_log_name, "w+")
	read_log = open(read_log_name, "r")
 
	sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	receiver_address = (reciever_ip, reciever_port)
	
	# start receive thread (modify as needed) which receives ACKs
	recv_thread = threading.Thread(target=receive_thread,args=(socket,))
	recv_thread.start()

    # your main thread can act as the send thread which sends data packets
    
	# take the input file and split it into packets (use create_packet)

	# while there are packets to send:
		# send packets to receiver using our unreliable_channel.send_packet()
		# update the window size, timer, etc.

