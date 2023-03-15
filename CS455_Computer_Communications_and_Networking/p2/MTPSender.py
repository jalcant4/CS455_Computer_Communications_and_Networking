## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import threading
import unreliable_channel


## define and initialize
# window_size, window_base, seq_number, dup_ack_count, etc.


## we will need a lock to protect against two concurrent threads
lock = threading.Lock()


def create_packet(..):
# create data packet
# crc32 available through zlib library


def extract_packet_info(..):
# extract the ack after receiving


def receive_thread(..):
	while True:
		# receive ack, but using our unreliable channel
		# packet_from_receiver, receiver_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption, take steps accordingly
		# update window size, timer, triple dup acks


def main(..):
	# some of the things to do:
    # open log file and start logging
    # read the command line arguments
	# open UDP socket

	# start receive thread (modify as needed) which receives ACKs
	recv_thread = threading.Thread(target=receive_thread,args=(socket,))
	recv_thread.start()

    # your main thread can act as the send thread which sends data packets
    
	# take the input file and split it into packets (use create_packet)

	# while there are packets to send:
		# send packets to receiver using our unreliable_channel.send_packet()
		# update the window size, timer, etc.

