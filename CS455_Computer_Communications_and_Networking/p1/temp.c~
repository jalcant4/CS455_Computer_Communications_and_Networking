/*
	Written by Jed Alcantara
 	G00846927
 	Written by Amit
 	G
	Last edited: 2/25/23
 * */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/socket.h>

time_t t;
srand(time(&t));

static int ID = rand() % 65536;

typedef struct header {
	int id; 	//ID: A 16-bit id that can uniquely identify a query message. Note that when you send multiple query
				//messages, you will use this ID to match the responses to queries. The ID can be randomly generated
				//by your client program.
	int flags;	//flags of which includes qr op rd
	int qr;		//QR: 0 for query and 1 for a response.
	int op; 	//OPCODE: We are only interested in a standard query, i.e., it is 0.
	int rd;		//RD: This bit is set if the client wants the name server to recursively pursue the query. We will set this
				//to 1.
	int qdcount;	//QDCOUNT: Since we are only sending one hostname query at a time, we will set this to 1
	int ancount;
	int nscount;
	int arcount;
} header_t = {ID, 0, 0, 0, 1, 1, 0, 0, 0};

int main {
	
}


