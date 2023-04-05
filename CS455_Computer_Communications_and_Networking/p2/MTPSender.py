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
PACKET_TIMEOUT = 0.5
MAX_DUP_ACKS = 3
SENDER_IP = "127.0.0.1"
SENDER_PORT = 8888

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

send_index = 0				# sender index

dup_ack_count = 0
exp_seq_num = 0				# the seqNum we are expecting in our ACK
last_ack_seq_num = 0		# the seqNum of the last_ackious ACK


packets = []				# contains packet by seqNum
acks = []					# contains ack by seqNum
ack_timers = {}				# contains 

## we will need a lock to protect against two concurrent threads
lock = threading.Lock()
mutex = threading.Lock()


def int_to_bytes(i):
    return i.to_bytes(4, byteorder='big')

def bytes_to_int(b):
    return int.from_bytes(b, byteorder='big')

def calc_checksum(type_data, seq_num, data_length, data):
    checksum = 0

    type_data = int_to_bytes(type_data)
    seq_num = int_to_bytes(seq_num)
    data_length = int_to_bytes(data_length)
    
	# Calculate checksum incrementally in chunks
    CHUNK_SIZE = 1024  # adjust chunk size as needed
    data_bytes = str(data).encode()
    for i in range(0, len(data_bytes), CHUNK_SIZE):
        chunk = data_bytes[i:i+CHUNK_SIZE]
        checksum = zlib.crc32(type_data + seq_num + data_length + chunk, checksum)

    return checksum.to_bytes(4, byteorder='big')


# MTP DATA packet looks as shown below. Note that your MTP header + data is encapsulated in the UDP
# header since the sender and receiver connect over a UDP socket. Of course, the UDP header is already
# added by the socket and is something that you don’t have to implement.
def create_data_packet(data, seq_num):
    # create data packet
    # crc32 available through zlib library
    type_data = b'DATA'
    seq_num = int_to_bytes(seq_num)
    data_length = int_to_bytes(len(data) + MTP_HEADER_SIZE)
    checksum = calc_checksum(bytes_to_int(type_data), bytes_to_int(seq_num), bytes_to_int(data_length), data)
    data = data.encode('utf-8')

    packet_format = '!4s4s4s4s' + str(len(data)) + 's'
    packet = struct.pack(packet_format, type_data, seq_num, data_length, checksum, data)
    return packet


def extract_packet_info(packet):
	mtp_header = packet[0:MTP_HEADER_SIZE]
	type_data = bytes_to_int(mtp_header[0:4])
	seq_num = bytes_to_int(mtp_header[4:8])
	data_length = bytes_to_int(mtp_header[8:12])
	checksum = bytes_to_int(mtp_header[12:16])

	return type_data, seq_num, data_length, checksum


# the purpose of the receive_thread is to receive ACKs
def receive_thread(r_socket):
	global receiver_address, exp_seq_num, last_ack_seq_num, dup_ack_count, lock, timer
	
	while len(acks) != len(packets):
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		packet_from_server, receiver_address = unreliable_channel.recv_packet(r_socket)
		ack_type_data, ack_seq_num, ack_data_length, ack_checksum = extract_packet_info(packet_from_server)

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
		time.sleep(0.1)


def send_packet(sender_socket, packet, receiver_address):
	global sender_log
	type_data, seq_num, data_length, checksum = extract_packet_info(packet)
	sender_log.write("Packet sent; type={}; seqNum={}; length={}; checksum={}".format(
		type_data, seq_num, data_length, checksum
	))
	unreliable_channel.send_packet(sender_socket, packet, receiver_address)

 
# only sends packets within the window
# assumption: must be ran after receive_thread
def send_thread(sender_socket, packets):
	global last_ack_seq_num, exp_seq_num, window, window_base, window_size, acks, ack_timers, timer, lock
	
	while len(acks) != len(packets):
		# set window
		with lock:
			window_base = window
			window = window_base + window_size

		# this loop send_packet
		while exp_seq_num < window:
			timer = Timer(PACKET_TIMEOUT)
			timer.start()
			ack_timers.append(timer)

			with lock:
				# timeout
				if timer.timeout() or not timer.is_running():
					sender_index = last_ack_seq_num + 1
					packet = packets[sender_index]
					send_packet(sender_socket, packet, receiver_address)
					timer.start()
				# are there packets to send
				elif sender_index != window:
					packet = packets[exp_seq_num]
					send_packet(sender_socket, packet, receiver_address)
					# Increment sequence number
					sender_index += 1
					timer().start()

			if last_ack_seq_num != window:
				# allow other thread to run until we receive ACKs
				time.sleep(0.1)
    

def main():
	global sender_socket, sender_address, packets, receiver_address, window_size, input, sender_log
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


	# start receive thread (modify as needed) which receives ACKs
	recv_thread = threading.Thread(target=receive_thread, args=(sender_socket,))
	recv_thread.start()

	
    # while there are packets to send:
	# send packets to receiver using our unreliable_channel.send_packet()
	# update the window size, timer, etc.
	snd_thread = threading.Thread(target=send_thread, args=(sender_socket, packets))
	snd_thread.start()
# your main thread can act as the send thread which sends data packets  
main()

