## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import numpy as np
import threading
import unreliable_channel
import socket
import sys
import struct
from Timer import Timer
import time
import zlib

# constant
UDP_HEADER_SIZE = 28
MTP_HEADER_SIZE = 16
MAX_DATA_SIZE = 1500 - UDP_HEADER_SIZE - MTP_HEADER_SIZE
ACK_TIMEOUT = 0.5
MAX_DUP_ACKS = 3
FINAL_SEQ_NUM = 2 ** 31

SENDER_IP = '127.0.0.1'
SENDER_PORT = 8001

# define and initialize
sender_address = (SENDER_IP, SENDER_PORT)
sender_socket = None

sender_log = None
output = None

receiver_address = None
receiver_socket = None

final_packet = None

window = 0
window_base = 0
window_size = 0

sender_index = 0			# sender index

dup_ack_count = 0
exp_seq_num = 0				# the seqNum we are expecting in our ACK
last_ack_seq_num = 0		# the seqNum of the last_ackious ACK

timer = None

packets = []				# contains packet by seqNum
acks = []					# contains ack by seqNum

## we will need a lock to protect against two concurrent threads
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
    CHUNK_SIZE = MAX_DATA_SIZE  # adjust chunk size as needed
    data_in_bytes = data.encode()
    for i in range(0, len(data_in_bytes), CHUNK_SIZE):
        chunk = data_in_bytes[i:i+CHUNK_SIZE]
        checksum = zlib.crc32(data_type_bytes + seq_num_bytes + data_length_bytes + chunk, checksum)

    return checksum.to_bytes(4, byteorder='big')


# MTP DATA packet looks as shown below. Note that your MTP header + data is encapsulated in the UDP
# header since the sender and receiver connect over a UDP socket. Of course, the UDP header is already
# added by the socket and is something that you don’t have to implement.
def create_data_packet(data, seq_num):
    # create data packet
    # crc32 available through zlib library
    data_type = b'DATA'
    seq_num = int_to_bytes(seq_num)
    data_length = int_to_bytes(len(data) + MTP_HEADER_SIZE)
    checksum = calc_checksum(data_type, seq_num, data_length, data)
    data = data.encode('utf-8')

    packet_format = "!4s4s4s4s{}s".format(len(data))
    packet = struct.pack(packet_format, data_type, seq_num, data_length, checksum, data)
    return packet


def extract_packet_info(packet):
    # Extract the MTP header from the packet
    mtp_header = packet[:MTP_HEADER_SIZE]
    
    # Unpack the values from the MTP header using the struct format
    data_type, seq_num, data_length, checksum = struct.unpack('!4s4s4s4s', mtp_header)
    
    # Convert the bytes objects to integer values
    data_type = data_type.decode('utf-8')
    seq_num = bytes_to_int(seq_num)
    data_length = bytes_to_int(data_length)
    checksum = bytes_to_int(checksum)
    
    return data_type, seq_num, data_length, checksum


# the purpose of the receive_thread is to receive ACKs
def receive_thread(r_socket):
	global receiver_address, exp_seq_num, last_ack_seq_num, dup_ack_count, lock, timer
	
	while len(acks) != len(packets):
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		packet_from_server, receiver_address = unreliable_channel.recv_packet(r_socket)
		ack_data_type, ack_seq_num, ack_data_length, ack_checksum = extract_packet_info(packet_from_server)

		if ack_data_type == b'ACK':
			# get packet that is ACKNOWLEDGED
			local_packet = packets[ack_seq_num]
			# parse checksum from local_packet
			local_data, local_seq_num, local_data_length, local_checksum = extract_packet_info(local_packet)

			if ack_seq_num != exp_seq_num:
				sender_log.write("Packet received; type={}; seqNum{}; length={}; checksum_in_packet={}; checksum_calculated={}; status=OUT_OF_ORDER;".format(
					ack_data_type, ack_seq_num, ack_data_length, ack_checksum, local_checksum
				))
				handle_out_of_order()

			# check for corruption, take steps accordingly
			elif local_checksum != ack_checksum:
				sender_log.write("Packet received; type={}; seqNum{}; length={}; checksum_in_packet={}; checksum_calculated={}; status=CORRUPT;".format(
					ack_data_type, ack_seq_num, ack_data_length, ack_checksum, local_checksum
				))
				# ignore if ACK is corrupted

		
			# update exp_seq_num and last_ack_seq_num
			elif local_checksum == ack_checksum:
				sender_log.write("Packet received; type={}; seqNum{}; length={}; checksum_in_packet={}; checksum_calculated={}; status=NOT_CORRUPT;".format(
					ack_data_type, ack_seq_num, ack_data_length, ack_checksum, local_checksum
				))
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

						if dup_ack_count == MAX_DUP_ACKS:
							handle_dup_acks(ack_seq_num + 1)
					
		time.sleep(0.1)


def send_packet(sender_socket, packet, receiver_address):
	global sender_log

	data_type, seq_num, data_length, checksum = extract_packet_info(packet)

	sender_log.write("Packet sent; type={}; seqNum={}; length={}; checksum={}\n".format(
		str(data_type), seq_num, data_length, checksum
	))
	unreliable_channel.send_packet(sender_socket, packet, receiver_address)

 
# only sends packets within the window
# assumption: must be ran after receive_thread
def send_thread(sender_socket, packets):
	global timer, lock
	
	while len(acks) != len(packets):
		#set window
		update_window(window)

		# send packets within window
		for i in range(window - window_base):
			packet = packets[window_base + i]
			send_packet(sender_socket, packet, receiver_address)

		#start timer
		if timer is None or not timer.is_running():
			timer = Timer(ACK_TIMEOUT, handle_timeout)
			timer.start()

		with lock:
			while last_ack_seq_num != window:
				# Wait for acks before sending next window
				time.sleep(0.1)

		if (len(acks) == len(packets)):
			break
	
	sender_socket.close()


# locks and protects the window
def update_window(start):
	global window, window_base

	window_base = start
	if window_base + window_size < len(packets):
		window = window_base + window_size
	else:
		window = window_base + (len(packets) - window_base)


def handle_timeout():
	global timer, dup_ack_count, exp_seq_num, lock

	update_window(last_ack_seq_num + 1)

	with lock:	
		# send packets within window range
		for i in range(window_size):
			packet = packets[window_base + i]
			send_packet(sender_socket, packet, receiver_address)

		timer = Timer(ACK_TIMEOUT, handle_timeout)
		timer.start()
        
        # Reset duplicate ack count and expected sequence number
		dup_ack_count = 0
		exp_seq_num = last_ack_seq_num + 1


def handle_out_of_order():
	global timer, dup_ack_count, exp_seq_num, lock

	update_window(last_ack_seq_num + 1)

	with lock:
		# send packets within window range
		for i in range(window_size):
			packet = packets[window_base + i]
			send_packet(sender_socket, packet, receiver_address)

		timer = Timer(ACK_TIMEOUT, handle_timeout)
		timer.start()
        
        # Reset duplicate ack count and expected sequence number
		dup_ack_count = 0
		exp_seq_num = last_ack_seq_num + 1


def handle_dup_acks(s_n):
	global timer, dup_ack_count, exp_seq_num, lock

	update_window(s_n)

	with lock:
		# send packets within window range
		for i in range(window_size):
			packet = packets[window_base + i]
			send_packet(sender_socket, packet, receiver_address)

		timer = Timer(ACK_TIMEOUT, handle_timeout)
		timer.start()
        
        # Reset duplicate ack count and expected sequence number
		dup_ack_count = 0
		exp_seq_num = last_ack_seq_num + 1


def main():
	global sender_socket, sender_address, receiver_address, window_size, packets, final_packet, input, sender_log

	try:
		# read the command line arguments
		receiver_ip = socket.gethostbyname(sys.argv[1])
		receiver_port = int (sys.argv[2])
		receiver_address = (receiver_ip, receiver_port)
		window_size = int (sys.argv[3])
		# open log file and start logging
		input = open (sys.argv[4], "r")
		sender_log = open (sys.argv[5], "w+")


		# open the UDP socket
		sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sender_log.write("Connecting sender socket ...\n")
		sender_socket.bind(sender_address)


		# creates packets
		seq_num = 0
		segment = input.read(MAX_DATA_SIZE)
		while segment:
			# append to list of packets
			packets.append(create_data_packet(segment, seq_num))
			# update
			segment = input.read(MAX_DATA_SIZE)
			seq_num +=1
		final_packet = create_data_packet("", FINAL_SEQ_NUM)
		packets.append(final_packet)
		sender_log.write("Finished creating packets ...\n")


		# start receive thread (modify as needed) which receives ACKs
		sender_log.write("Opening receiver channel ...\n")
		recv_thread = threading.Thread(target=receive_thread, args=(sender_socket,))
		recv_thread.start()

		# while there are packets to send:
		# send packets to receiver using our unreliable_channel.send_packet()
		# update the window size, timer, etc.
		sender_log.write("Starting to send packets ...\n")
		snd_thread = threading.Thread(target=send_thread, args=(sender_socket, packets))
		snd_thread.start()

		recv_thread.join()
		snd_thread.join()

	finally:
		sender_socket.close()
		sender_log.close()
		input.close()

# your main thread can act as the send thread which sends data packets  
main()