#include <stdio.h>
#include <stdlib.h>

typedef struct header {
	int id; //ID: A 16-bit id that can uniquely identify a query message. Note that when you send multiple query
		//messages, you will use this ID to match the responses to queries. The ID can be randomly generated
		//by your client program.
	int qr;	//QR: 0 for query and 1 for a response.
	int op; //OPCODE: We are only interested in a standard query, i.e., it is 0.
	int rd;	//RD: This bit is set if the client wants the name server to recursively pursue the query. We will set this
		//to 1.
	int qd;	//QDCOUNT: Since we are only sending one hostname query at a time, we will set this to 1
} header_t;

:

int main {

}
