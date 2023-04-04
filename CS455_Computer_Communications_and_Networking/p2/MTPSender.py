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

#constant
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
exp_seq_num = 0
last_seq_num = 0


packets = []
acks = []

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
			sender_log.write(f"Packet received; type={type_data}; seqNum={next_seq_num}; length={data_length}; checksum_in_packet={checksum}; checksum_calculated={validate_checksum}; status=CORRUPT;")
		elif checksum == validate_checksum:
			if window_base == next_seq_num:
				dup_ack_count += 1
				if dup_ack_count == 3:
					mutex.acquire()
					next_seq_num = window_base
					dup_ack_count = 0
					sender_log.write("Triple Dup ACK received for packet seqNum= {window_base}")
					mutex.release()
			if window_base < next_seq_num:
				mutex.acquire()
				next_seq_num -= 1
				sender_log.write("Acks received from the receiver for the seqeuence number {next_seq_num}.\n Udaating window from {window_base} to {nex_seq_num}\n")
				window_base = next_seq_num
				#TODO timeout
				if packet_timeout is not None:
					packet_timeout.stop()
				mutex.release()
     
       	
def parse_header(packet):
    type_data, seq_num, data_length, checksum = extract_packet_info(packet)
    
    return "type_data= {}; seqNum = {}; data_length = {}; checksum = {}".format(
        type_data, seq_num, data_length, hex(checksum)[2:]
    )
    

def receive_thread(r_socket):
	global exp_seq_num, last_seq_num, dup_ack_count, lock
	while exp_seq_num < len(packets):
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		packet_from_server, server_addr = unreliable_channel.recv_packet(r_socket)
		type_data, seq_num, data_length, receiver_checksum = extract_packet_info(packet_from_server)
		
		if type_data == b'ACK':
			# check for corruption, take steps accordingly
			sender_checksum = packets[seq_num]
			if sender_checksum != receiver_checksum:
				# ignore if ACK is corrupted
				continue
		
			# update exp_seq_num and last_seq_num
			elif sender_checksum == receiver_checksum:
				with lock:
					if seq_num == exp_seq_num:
						last_seq_num = exp_seq_num
						exp_seq_num += 1
						dup_ack_count = 0
					#update triple dup acks
					elif seq_num <= last_seq_num:
						dup_ack_count += 1

						if dup_ack_count == 3:
							exp_seq_num = seq_num
							dup_ack_count = 0


def send_packet(sender_socket, packet, receiver_address):
	unreliable_channel.send_packet(sender_socket, packet, receiver_address)

def send_thread(sender_socket, packets):
	global last_seq_num, exp_seq_num, window_base, window_size, acks, timer, lock

	timer = Timer(PACKET_TIMEOUT,)
	
	while window_base < len(packets):
		with lock:
			# update window
			window = window_base + window_size
			if (exp_seq_num >= window):
				window_base = window

		with lock:	
			# are there packets to send
			if exp_seq_num <= len(packets):
				packet = packets(exp_seq_num)
				send_packet(sender_socket, packet, receiver_address)

				timer.start()
				# Increment sequence number
				exp_seq_num += 1

		while timer.isRunning() and not timer.timeout():
			time.sleep(0.1)
		
		with lock:
			send_packet(sender_socket, packet, receiver_address)
			timer.start()

def main():
	global packets, reciever_ip, reciever_port, receiver_address, window_size, input, sender_log
    # read the command line arguments
	reciever_ip = sys.argv[1]
	reciever_port = int (sys.argv[2])
	receiver_address = (reciever_ip, reciever_port)
	window_size = int (sys.argv[3])
	# open log file and start logging
	#input = open (sys.argv[4], "rw+")
	#sender_log = open (sys.argv[5], "rw+")
	input = open (sys.argv[4], "w+")
	sender_log = open (sys.argv[5], "r")

	# open the UDP socket
	sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	receiver_address = (sender_ip, sender_port)
	#sender_socket.bind(receiver_address)
	
	# take the input file and split it into packets
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
	while window_base < final_packet:
		#a = window_base > max_window_size
		#b = next_seq_number < final_packet
		
		mutex.acquire()
		#while a and b:
		while window_base > max_window_size and next_seq_number < final_packet:
			#sender_log_file.write("Sending packet with seqNum: {} \n". format(next_seq_number))
			unreliable_channel.send_packet(sender_socket, packets[next_seq_number], receiver_address)

			#log the sender packate info into
			sender_log.write("Packet sent; {}\n". format(parse_header(packets[next_seq_number])))

			next_seq_number += 1
		packet_timeout.start()
		mutex.release()
		
  		# Yield to other threads
		while packet_timeout.is_running() and packet_timeout.timeout() is False:
			time.sleep(0)
		
		mutex.acquire()
		# did not successfully received ack, update window_base
		if packet_timeout.timeout():  
			sender_log.write("Timeout  for packet seqNum= {next_seq_number}\n")
			next_seq_number = window_base
		mutex.release()
  
	sender_log.write("Final packet sent : {next_seq_number}\n")
	unreliable_channel.send_packet(sender_socket, create_packet('', next_seq_number), receiver_address)
	# send packets to receiver using our unreliable_channel.send_packet()
	# update the window size, timer, etc.
	send_thread = threading.Thread(target=send_thread, args=(sender_socket,packets))
	send_thread.start()
     
# your main thread can act as the send thread which sends data packets  
main()

