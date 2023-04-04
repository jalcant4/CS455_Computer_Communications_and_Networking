## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import threading
import unreliable_channel
import numpy as np
import zlib
from Timer import Timer
import time
import socket
import sys

## define and initialize
# rec_window_size, rec_window_base, seq_number, dup_ack_count, etc.
sender_addr = None
required_seq_num = 0
receiver_log = None
receiver_socket = None
out_txt = None
ack_timeout = Timer(0.5)

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
	return type_data, seq_num, data_length, checksum, packet[16:].decode('utf-8')

def validate_header(packet, validate_checksum):
    type_data, seq_num, data_length, checksum = extract_packet_info(packet)
    valid = ""
    x = bytes_to_int(validate_checksum)
    if(checksum != x):
        valid = "Corrupt"
    else:
        valid = "Not Corrupt"   
    return "type_data= {}; seqNum = {}; data_length = {}; checksum = {}; valid = {}".format(
        type_data, seq_num, data_length, hex(checksum)[2:], valid)
    
def send_ack():
    if sender_addr is not None:
        receiver_log.write("Ack with sequence num sent: {required_seq_num}\n")
        packet = create_packet('',required_seq_num)
        unreliable_channel.send_packet(receiver_socket, packet, sender_addr)

def send_thread(socket):
    while True:
        # send ack packets but using unreliable channel
        # update window size, timer, triple dup acks
        packet_from_server, sender_addr = unreliable_channel.recv_packet(socket)
        type_data, seqNum, data_length, checksum, data = extract_packet_info(packet_from_server)

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
        
    # start send thread that sends back the acks (modify as needed)
    send_thread = threading.Thread(target=send_thread,args=[receiver_socket])
    send_thread.start()
    send_thread.join()
    
    # while there packets being received:
    while(1):
		# receive packet, but using our unreliable channel
		# packet_from_sender, sender_addr = unreliable_channel.recv_packet(socket)
        packet_from_sender, sender_addr = unreliable_channel.recv_packet(receiver_socket)
        # call extract_packet_info
        type_data, seq_num, data_length, checksum, data = extract_packet_info(packet_from_sender)
		# check for corruption and lost packets, send ack accordingly
        send_thread()
        if data == '' or data is None:
            break
    
    packet = create_packet('', 0)
    unreliable_channel.send_packet(receiver_socket,packet, sender_addr)

# your main thread can act as the receive thread that receives DATA packets
main()


