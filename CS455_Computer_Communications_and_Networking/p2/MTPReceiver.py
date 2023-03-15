## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more as you need)
import threading
import unreliable_channel


## define and initialize
# rec_window_size, rec_window_base, seq_number, dup_ack_count, etc.


## we will need a lock to protect against two concurrent threads
lock = threading.Lock()


def create_packet(..):
# create ack packet
# crc32 available through zlib library


def extract_packet_info(..):
# extract the data packet after receiving


def send_thread(..):
    while True:
        # send ack packets but using unreliable channel
        # update window size, timer, triple dup acks


def main(..):
    # Some of the things to do:
    # open log file and start logging
	# read the command line arguments
	# open UDP socket

    # start send thread that sends back the acks (modify as needed)
    send_thread = threading.Thread(target=send_thread,args=(socket,))
    send_thread.start()

    # your main thread can act as the receive thread that receives DATA packets

	# while there packets being received:
		# receive packet, but using our unreliable channel
		# packet_from_sender, sender_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption and lost packets, send ack accordingly


