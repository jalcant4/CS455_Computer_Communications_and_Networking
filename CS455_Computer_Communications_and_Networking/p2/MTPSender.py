## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import numpy as np
import threading
import unreliable_channel
import zlib
import socket
import sys
from Timer import Timer
import time

# constant
UDP_HEADER_SIZE = 28
MTP_HEADER_SIZE = 16
MAX_DATA_SIZE = 1500 - UDP_HEADER_SIZE - MTP_HEADER_SIZE
PACKET_TIMEOUT = 0.5
MAX_DUP_ACKS = 3

# define and initialize
sender_ip = None
sender_port = None
sender_log = None
output = None
packet_timeout = None
final_packet = None

window_base = 0
window_size = 0
max_window_size = 0

dup_ack_count = 0
exp_seq_num = 0				# the seqNum we are expecting in our ACK
last_ack_seq_num = 0			# the seqNum of the last_ackious ACK


packets = []				# contains packet by seqNum
acks = []					# TODO: contains ack by seqNum

timer = None

## we will need a lock to protect against two concurrent threads
lock = threading.Lock()
mutex = threading.Lock()

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

def getCurrWindowSize(totalpackets, window_size):
    return min(window_size, totalpackets - window_base + 1)

# MTP DATA packet looks as shown below. Note that your MTP header + data is encapsulated in the UDP
# header since the sender and receiver connect over a UDP socket. Of course, the UDP header is already
# added by the socket and is something that you don’t have to implement.
def create_packet(data, seq_num):
	# create data packet
	# crc32 available through zlib library
	type_data = b'DATA'  
	seq_num = int_to_bytes(seq_num)
	data_length = int_to_bytes(len(data))
	checksum = calc_checksum(type_data, seq_num, data_length, data)
	data = bytes(data, 'utf-8')
	return type_data + seq_num + data_length + checksum + data

def extract_packet_info(packet):
	# extract the ack after receiving
	mtp_header = packet[0:MTP_HEADER_SIZE]
	type_data = bytes_to_int(mtp_header[0:4])
	seq_num = bytes_to_int(mtp_header[4:8])
	data_length = bytes_to_int(mtp_header[8:12])
	checksum = bytes_to_int(mtp_header[12:16])

	return type_data, seq_num, data_length, checksum
       	
def parse_header(packet):
    type_data, seq_num, data_length, checksum = extract_packet_info(packet)
    
    return "type_data= {}; seqNum = {}; data_length = {}; checksum = {}".format(
        type_data, seq_num, data_length, hex(checksum)[2:]
    )
    
# the purpose of the receive_thread is to receive ACKs
# TODO: timer
def receive_thread(r_socket):
	global receiver_address, exp_seq_num, last_ack_seq_num, dup_ack_count, lock, timer
	while len(acks) != len(packets):
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		packet_from_server, receiver_address = unreliable_channel.recv_packet(r_socket)
		ack_type_data, ack_seq_num, ack_data_length, ack_checksum = extract_packet_info(packet_from_server)
		
		# timer is initialized and started
		if timer is None or not timer.is_running:
			timer = Timer(PACKET_TIMEOUT)
			timer.start()

		if ack_type_data == b'ACK':
			# get packet that is ACKNOWLEDGED
			local_packet = packets[ack_seq_num]
			# parse checksum from local_packet
			local_data, local_seq_num, local_data_length, local_checksum = extract_packet_info(local_packet)
			# check for corruption, take steps accordingly
			if local_checksum != ack_checksum:
				# ignore if ACK is corrupted
				continue
		
			# update exp_seq_num and last_ack_seq_num
			elif local_checksum == ack_checksum:
				with lock:
					# if we get the expected sequence number, update
					#	exp_seq_num is incremented
					#	last_ack_seq_num is a comparison value in case of dup ACKs
					#	reset the dup ack_count
					if ack_seq_num == exp_seq_num:
						acks.append(packet_from_server)
						last_ack_seq_num = exp_seq_num
						exp_seq_num += 1
						dup_ack_count = 0
					# update triple dup acks
					elif ack_seq_num <= last_ack_seq_num:
						dup_ack_count += 1

						if dup_ack_count == 3:
							exp_seq_num = ack_seq_num
							dup_ack_count = 0
       # timeout stops the timer essentially restarting the timer in the receive thread
		if timer.timeout():
			exp_seq_num = exp_seq_num
			timer.stop()
		# allow other thread to run
		time.sleep(0.1)


def send_packet(sender_socket, packet, receiver_address):
	unreliable_channel.send_packet(sender_socket, packet, receiver_address)
 
# only sends packets within the window
# assumption: must be ran after receive_thread
def send_thread(sender_socket, packets):
	global last_ack_seq_num, exp_seq_num, window_base, window_size, acks, timer, lock
 
	window =  window_base + window_size
	while exp_seq_num < window:
		with lock:
			# update window
			if (exp_seq_num >= window):
				window_base = window
			window = window_base + window_size

		with lock:
			packet = packets(exp_seq_num)
			if timer.timeout() or not timer.is_running():
				send_packet(sender_socket, packet, receiver_address)
			# are there packets to send
			elif exp_seq_num <= len(packets):
				send_packet(sender_socket, packet, receiver_address)
				# Increment sequence number
				exp_seq_num += 1
		# allow other thread to run
		time.sleep(0.1)
    

def main():
	global packets, reciever_ip, reciever_port, receiver_address, window_size, input, sender_log
    # read the command line arguments
	reciever_ip = sys.argv[1]
	reciever_port = int (sys.argv[2])
	receiver_address = (reciever_ip, reciever_port)
	window_size = int (sys.argv[3])
	# open log file and start logging
	input = open (sys.argv[4], "w+")
	sender_log = open (sys.argv[5], "r")


	# open the UDP socket
	sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sender_address = (sender_ip, sender_port)
	sender_socket.bind(sender_address)
	
 
	# creates packets
	seq_num = 0
	segment = input.read(MAX_DATA_SIZE)
	while input:
		# append to list of packets
		packets.append(create_packet(segment, seq_num))
		# update
		segment = input.read(MAX_DATA_SIZE)
		seq_num +=1


	# start receive thread (modify as needed) which receives ACKs
	recv_thread = threading.Thread(target=receive_thread, args=(sender_socket,))
	recv_thread.start()

	
     # while there are packets to send:
	# send packets to receiver using our unreliable_channel.send_packet()
	# update the window size, timer, etc.
	send_thread = threading.Thread(target=send_thread, args=(sender_socket, packets))
	send_thread.start()
# your main thread can act as the send thread which sends data packets  
main()

