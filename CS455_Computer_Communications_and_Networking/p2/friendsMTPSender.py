## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish
## import (add more if you need)


from ast import Assign
from concurrent.futures.thread import _global_shutdown_lock
from glob import glob
from struct import pack
import threading

from matplotlib.pyplot import bar_label
import unreliable_channel
import socket
import zlib
import math
import sys
import time
from Timer import Timer

## global variable
MAX_DATA_SIZE = 1456

## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.
window_base = 0; next_seq_number = 0; dup_ack_count = 0; window_size = 0; total_packets = 0; max_window_size = 0
packet_timeout_timer = Timer(0.5)
mutex = threading.Lock()
sender_log_file = None

# client_port
## we will need a lock to protect against concurrent threads
lock = threading.Lock()

def getCurrWindowSize(total_packets, window_size):
	return min(window_size, total_packets - window_base + 1)


def intToBytes(num):
	return num.to_bytes(4, byteorder='little', signed=False)

def bytesToInt(byte):
	return int.from_bytes(byte, 'little', signed= False)


def calc_checksum(b1, b2, b3):
	if type(b1) is int:
		b1 = intToBytes(b1)
		b2 = intToBytes(b2)
		b3 = intToBytes(b3)
	return intToBytes(zlib.crc32(b1+b2+b3))



def create_packet(data, seqNum):
# Two types of packets, data and ack
# crc32 available through zlib library
	type_data = b'data'  
	seqNum = intToBytes(seqNum)
	length_data = intToBytes(len(data) + 16)
	checksum = calc_checksum(type_data, seqNum, length_data)
	data = bytes(data, 'utf-8')
	return type_data + seqNum + length_data + checksum + data


def extract_packet_info(packet):
	# extract the packet data after receiving
	mtp_header = packet[0:16]
	type_data = bytesToInt(mtp_header[0:4])
	seqNum = bytesToInt(mtp_header[4:8])
	data_length = bytesToInt(mtp_header[8:12])
	checksum = bytesToInt(mtp_header[12:16])
	return type_data, seqNum, data_length, checksum

def headerBreakdown(packet):
	type_data, seqNum, data_length, checksum = extract_packet_info(packet)
	return f"types= {type_data}; seqNum = {seqNum}; length =  {data_length} checksum = {hex(checksum)[2:]}"


def receive_thread(sender_socket):
	global window_base
	global window_size
	global dup_ack_count
	global next_seq_number
	global mutex

	while True:
		# receive packet, but using our unreliable channel
		# packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption, take steps accordingly
		# update window size, timer, triple dup acks
		packet_from_server, server_addr = unreliable_channel.recv_packet(sender_socket)
		type_data, nextSeqNum, data_length, checksum = extract_packet_info(packet_from_server)
		
		# seq number with 0 signfies receiver is done sending ack
		if nextSeqNum == 0:
			break
		#check for corrupted data
		if checksum != bytesToInt(calc_checksum(type_data, nextSeqNum, data_length)):
			sender_log_file.write("Corruped data while receiving ack with next seq no" + str(nextSeqNum) + ". Ignoring it. \n")
		else:
			# triple dup acks
			if nextSeqNum == window_base :
				dup_ack_count += 1
				if dup_ack_count == 3:
					mutex.acquire()
					next_seq_number = window_base
					dup_ack_count =0
					sender_log_file.write("triple dup detected for seq_num: {}".format(window_base))
					mutex.release()

			if nextSeqNum > window_base:
				mutex.acquire()
				sender_log_file.write("Successfully received ack from seqNum {}. Updating windowbase from {} to {} \n".format(nextSeqNum-1, window_base, nextSeqNum))
				window_base = nextSeqNum
				if packet_timeout_timer is not None:
					packet_timeout_timer.stop()
				mutex.release()



def main():
	global window_base
	global next_seq_number
	global dup_ack_count
	global mutex
	global sender_log_file
	global window_size
	global total_packets
	global max_window_size

	# read the command line arguments
	reciever_ip = sys.argv[1]
	reciever_port = int(sys.argv[2])
	max_window_size = int(sys.argv[3])
	data_file_name = sys.argv[4]
	sender_log_filename = sys.argv[5]
	
	# open data and log file
	sender_log_file = open(sender_log_filename, "w+")
	data_file = open(data_file_name, 'r')

	# open client socket and bind
	sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	receiver_address = (reciever_ip, reciever_port)


	# take the input file and split it into packets (use create_packet)
	packets = []
	seq_counter = 0
	while True:
		chunk = data_file.read(MAX_DATA_SIZE)
		if chunk == '' or chunk is None:
			break
		packets.append(create_packet(chunk, seq_counter))
		seq_counter += 1
		

	total_packets = len(packets)
	
	
	# while there are packets to send:
	# send packets to server using our unreliable_channel.send_packet()
	# window_size = getCurrWindowSize(len(packets), max_window_size)
	window_base = 0
	next_seq_number = 0

	# start receive thread
	recv_thread = threading.Thread(target=receive_thread, args=[sender_socket])
	recv_thread.start()

	while window_base < total_packets:
		#print(window_base, window_size, next_seq_number)
		mutex.acquire()
		while next_seq_number < window_base + max_window_size and next_seq_number < total_packets:
			#sender_log_file.write("Sending packet with seqNum: {} \n". format(next_seq_number))
			unreliable_channel.send_packet(sender_socket, packets[next_seq_number], receiver_address)

			#log the sender packate info into
			sender_log_file.write("Packet sent; {}\n". format(headerBreakdown(packets[next_seq_number])))

			next_seq_number += 1
		packet_timeout_timer.start()	
		# give chance for other thread to stop timer
		# very hard to control mutex with threading.Timer :(
		while packet_timeout_timer.is_running() and packet_timeout_timer.timeout() is False:
			mutex.release()
			time.sleep(0.01)
			mutex.acquire()

		# successfully received ack
		if not packet_timeout_timer.timeout(): 
			window_size = min(max_window_size, total_packets-window_base+1)
		else : 
			sender_log_file.write("Timeout while waiting for packet with seqNum: {}. Updating the next_seq_num from {} to {} \n". format(
				window_base, next_seq_number, window_base))
			next_seq_number = window_base
		mutex.release()
	
	# empty packet
	sender_log_file.write("Sending last packet: {} \n". format(next_seq_number))
	unreliable_channel.send_packet(sender_socket, create_packet('', next_seq_number), receiver_address)


main()