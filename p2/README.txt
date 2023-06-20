README


The MTPReceiver.py and the MTPSender.py must be in the same folder.


MTPReceiver.py must be called first.


The receiver can correctly extract all of 1MB.txt if we use this argument
	python3 ./MTPReceiver.py 8000 output.txt recv_log.txt
	python3 ./MTPSender.py 127.0.0.0 8000 688 1MB.txt sndr_log.txt

However an example arguments we suggest are:
	python3 ./MTPReceiver.py 8000 output.txt recv_log.txt
	python3 ./MTPSender.py 127.0.0.0 8000 30 1MB.txt sndr_log.txt


However, this ends up within an error in the SENDER:
	
Connecting sender socket ...
Finished creating 688 packets ...
Opening receiver channel ...
Starting to send packets ...
Window_base:0 Window:30
Packet sent; type=DATA; seqNum=0; length=1472; checksum=0e162119
Packet sent; type=DATA; seqNum=1; length=1472; checksum=9bb5ce42
Packet sent; type=DATA; seqNum=2; length=1472; checksum=2c4f691e
Packet sent; type=DATA; seqNum=3; length=1472; checksum=fa1684e4
Packet sent; type=DATA; seqNum=4; length=1472; checksum=eaa3a2b4
Packet sent; type=DATA; seqNum=5; length=1472; checksum=45c54461
Packet sent; type=DATA; seqNum=6; length=1472; checksum=8804ebf7
Packet sent; type=DATA; seqNum=7; length=1472; checksum=e342a28a
Packet sent; type=DATA; seqNum=8; length=1472; checksum=e8dd3c32
Packet sent; type=DATA; seqNum=9; length=1472; checksum=40149e69
Packet sent; type=DATA; seqNum=10; length=1472; checksum=a18566c9
Packet sent; type=DATA; seqNum=11; length=1472; checksum=1ddd05f8
Packet sent; type=DATA; seqNum=12; length=1472; checksum=956e06a1
Packet sent; type=DATA; seqNum=13; length=1472; checksum=4f2f917c
Packet sent; type=DATA; seqNum=14; length=1472; checksum=4b2b698f
Packet sent; type=DATA; seqNum=15; length=1472; checksum=03054827
Packet sent; type=DATA; seqNum=16; length=1472; checksum=bf533b77
Packet sent; type=DATA; seqNum=17; length=1472; checksum=b0093bc8
Packet sent; type=DATA; seqNum=18; length=1472; checksum=8ba7233d
Packet sent; type=DATA; seqNum=19; length=1472; checksum=cf63c3c9
Packet sent; type=DATA; seqNum=20; length=1472; checksum=fd47414c
Packet sent; type=DATA; seqNum=21; length=1472; checksum=dc199afb
Packet_received; type=_ACK; seqNum=0; length=16; checksum_in_packet=0e162119; checksum_calculated=0e162119; status=NOT_CORRUPT;
Packet_received; type=_ACK; seqNum=0; length=16; checksum_in_packet=0e162119; checksum_calculated=0e162119; status=OUT_OF_ORDER;
Packet_received; type=_ACK; seqNum=0; length=16; checksum_in_packet=0e162119; checksum_calculated=0e162119; status=OUT_OF_ORDER;
Packet_received; type=_ACK; seqNum=0; length=16; checksum_in_packet=0e162119; checksum_calculated=0e162119; status=OUT_OF_ORDER;
Handling Triple Dup ACKs


Although the receiver has received the packets in order, and sent ACKs in order:

MTP Receiver is connecting .
MTP Receiver is connecting ..
MTP Receiver is connecting ...
Packet_received: type=DATA; seqNum=0; length=1472; checksum_in_packet=0e162119; calculated_checksum=0e162119; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=0; length=16; checksum_in_packet=0e162119;
Packet_received: type=DATA; seqNum=1; length=1472; checksum_in_packet=9bb5ce42; calculated_checksum=9bb5ce42; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=1; length=16; checksum_in_packet=9bb5ce42;
Packet_received: type=DATA; seqNum=2; length=1472; checksum_in_packet=2c4f691e; calculated_checksum=2c4f691e; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=2; length=16; checksum_in_packet=2c4f691e;
Packet_received: type=DATA; seqNum=3; length=1472; checksum_in_packet=fa1684e4; calculated_checksum=fa1684e4; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=3; length=16; checksum_in_packet=fa1684e4;
Packet_received: type=DATA; seqNum=4; length=1472; checksum_in_packet=eaa3a2b4; calculated_checksum=eaa3a2b4; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=4; length=16; checksum_in_packet=eaa3a2b4;
Packet_received: type=DATA; seqNum=5; length=1472; checksum_in_packet=45c54461; calculated_checksum=45c54461; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=5; length=16; checksum_in_packet=45c54461;
Packet_received: type=DATA; seqNum=6; length=1472; checksum_in_packet=8804ebf7; calculated_checksum=8804ebf7; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=6; length=16; checksum_in_packet=8804ebf7;
Packet_received: type=DATA; seqNum=7; length=1472; checksum_in_packet=e342a28a; calculated_checksum=e342a28a; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=7; length=16; checksum_in_packet=e342a28a;
Packet_received: type=DATA; seqNum=8; length=1472; checksum_in_packet=e8dd3c32; calculated_checksum=e8dd3c32; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=8; length=16; checksum_in_packet=e8dd3c32;
Packet_received: type=DATA; seqNum=9; length=1472; checksum_in_packet=40149e69; calculated_checksum=40149e69; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=9; length=16; checksum_in_packet=40149e69;
Packet_received: type=DATA; seqNum=10; length=1472; checksum_in_packet=a18566c9; calculated_checksum=a18566c9; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=10; length=16; checksum_in_packet=a18566c9;
Packet_received: type=DATA; seqNum=11; length=1472; checksum_in_packet=1ddd05f8; calculated_checksum=1ddd05f8; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=11; length=16; checksum_in_packet=1ddd05f8;
Packet_received: type=DATA; seqNum=12; length=1472; checksum_in_packet=956e06a1; calculated_checksum=956e06a1; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=12; length=16; checksum_in_packet=956e06a1;
Packet_received: type=DATA; seqNum=13; length=1472; checksum_in_packet=4f2f917c; calculated_checksum=4f2f917c; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=13; length=16; checksum_in_packet=4f2f917c;
Packet_received: type=DATA; seqNum=14; length=1472; checksum_in_packet=4b2b698f; calculated_checksum=4b2b698f; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=14; length=16; checksum_in_packet=4b2b698f;
Packet_received: type=DATA; seqNum=15; length=1472; checksum_in_packet=03054827; calculated_checksum=03054827; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=15; length=16; checksum_in_packet=03054827;
Packet_received: type=DATA; seqNum=16; length=1472; checksum_in_packet=bf533b77; calculated_checksum=bf533b77; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=16; length=16; checksum_in_packet=bf533b77;
Packet_received: type=DATA; seqNum=17; length=1472; checksum_in_packet=b0093bc8; calculated_checksum=b0093bc8; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=17; length=16; checksum_in_packet=b0093bc8;
Packet_received: type=DATA; seqNum=18; length=1472; checksum_in_packet=8ba7233d; calculated_checksum=8ba7233d; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=18; length=16; checksum_in_packet=8ba7233d;
Packet_received: type=DATA; seqNum=19; length=1472; checksum_in_packet=cf63c3c9; calculated_checksum=cf63c3c9; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=19; length=16; checksum_in_packet=cf63c3c9;
Packet_received: type=DATA; seqNum=20; length=1472; checksum_in_packet=fd47414c; calculated_checksum=fd47414c; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=20; length=16; checksum_in_packet=fd47414c;
Packet_received: type=DATA; seqNum=21; length=1472; checksum_in_packet=dc199afb; calculated_checksum=dc199afb; status=NOT CORRUPT
Packet sent; type=_ACK; seqNum=21; length=16; checksum_in_packet=dc199afb;
Packet_received: type=DATA; seqNum=1; length=1472; checksum_in_packet=9bb5ce42; calculated_checksum=9bb5ce42; status=OUT OF ORDER PACKET