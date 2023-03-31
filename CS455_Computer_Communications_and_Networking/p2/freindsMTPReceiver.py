## The code provided here is just a skeleton that can help you get started
## You can add/remove functions and it's parameters as you wish

## imports (add more if you need)
from struct import pack_into

from numpy import byte, rec
import unreliable_channel
import threading 
import socket
import zlib
import time
import sys
import codecs
from Timer import Timer

def intToBytes(num):
	return num.to_bytes(4, byteorder='little', signed=False)

def bytesToInt(byte):
	return int.from_bytes(byte, 'little', signed=False)

#calculate checksum using 
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
	checksum =  calc_checksum(type_data, seqNum, length_data)
	data = bytes(data, 'utf-8')
	return type_data + seqNum + length_data + checksum + data


def extract_packet_info(packet):
	# extract the packet data after receiving
	mtp_header = packet[0:16]
	type_data = bytesToInt(mtp_header[0:4])
	seqNum = bytesToInt(mtp_header[4:8])
	data_length = bytesToInt(mtp_header[8:12])
	checksum = bytesToInt(mtp_header[12:16])
	data = packet[16:].decode('utf-8')
	return type_data, seqNum, data_length, checksum, data


def headerBreakdown(packet, exp_checksum):
	type_data,seqNum, data_length,checksum,data = extract_packet_info(packet)
	status = ""
	if(checksum == bytesToInt(exp_checksum)):
		status = "NOT_CURRUPT"
	else:
		status = "CURRUPT"
	return f"types= {type_data}; seqNum = {seqNum}; length =  {data_length}; checksum = {hex(checksum)[2:]}; status = {status}"


expected_seq_num = 0
client_addr = None
receiver_socket = None
receiver_log_file = None
output_file = None
ack_timeout_timer = None

def send_ack():
	global expected_seq_num
	if client_addr is not None:
		receiver_log_file.write("Sending ack  with seqNum : {}. \n".format(expected_seq_num))
		packet = create_packet('', expected_seq_num)
		unreliable_channel.send_packet(receiver_socket, packet , client_addr)
	

def receive_thread(socket):
	global expected_seq_num
	global ack_timeout_timer
	global client_addr
	
	while True:
		# receive packet, but using our unreliable channel
		# packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
		# store it in a buffer
		packet_from_server, client_addr = unreliable_channel.recv_packet(socket)
		type_data, seqNum, data_length, checksum, data = extract_packet_info(packet_from_server)

		if data == '' or data is None: 
			break

		#log recieved file on file
		receiver_log_file.write("Packet recieved; {} \n".format(headerBreakdown(packet_from_server, calc_checksum(type_data, seqNum, data_length))))

		#check for corrupted data
		if checksum != bytesToInt(calc_checksum(type_data, seqNum, data_length)):
			receiver_log_file.write("Corrupted data while receiving packet with seqNum: {} \n".format(seqNum))
		# done with receiving packets
		else : 
			receiver_log_file.write("Successfuly recieved the packet with seqNum: {} \n".format(seqNum))

			if seqNum > expected_seq_num:
				receiver_log_file.write("Package with seqNum: {} out of order while expecting seq: {} Sending dup ack with seqNum : {}. \n".format(seqNum, expected_seq_num, expected_seq_num))
				send_ack()
			else: 
				expected_seq_num = seqNum + 1
				output_file.write(data)
				if ack_timeout_timer is not None and ack_timeout_timer.is_alive() : 
					# was waiting for second packet and got it 
					ack_timeout_timer.cancel()
					send_ack()
				else :
					ack_timeout_timer = threading.Timer(500, send_ack)
					ack_timeout_timer.start()
			

def main():
	global receiver_socket
	global receiver_log_file
	global output_file
	# read the command line arguments
	# open log file and start logging
	# open server socket and bind
	# read the command line arguments
	reciever_ip = sys.argv[1]
	reciever_port = int(sys.argv[2])
	output_file = sys.argv[3]
	receiver_log_file = sys.argv[4]

	receiver_log_file = open(receiver_log_file, 'w+')
	output_file = open(output_file, 'w+')
	receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print("Connecting......")
	server_address = (reciever_ip, reciever_port)

	receiver_socket.bind(server_address)

	# start receive thread
	recv_thread = threading.Thread(target=receive_thread,args=[receiver_socket])
	recv_thread.start()	
	recv_thread.join()

	packet = create_packet('', 0)
	unreliable_channel.send_packet(receiver_socket, packet, client_addr)

main()