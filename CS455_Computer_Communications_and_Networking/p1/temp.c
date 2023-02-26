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
#include <string.h>
#include <sys/socket.h>

#define MAX 100

time_t t;
srand(time(&t));

static int ID = rand() % 65536;

//header
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
} header_t;
#define INIT_HEADER(X) header_t X = {ID, 0, 0, 0, 1, 1, 0, 0, 0};

//query
typedef struct query {
	  char name[MAX];
	  int dnstype;
	  int dnsclass;
} query_t;
#define INIT_QUERY(X, Y) query_t X = {.name = Y, 0, 0}

static INIT_HEADER(header);
static INIT_QUERY(query, "none");

void parse_qname(char *host);
int *init_dns_request();

int main {
	
}

void parse_qname(char *hostname) {
	if (hostname == NULL) { 
		
		exit(1);
	}

	header_t *query_p = &query;
	// it contains multiple labels - one for each section of a URL. For example, for gmu.edu, there should
	// be two labels for gmu and edu. Each label consists of a length octet (3 for gmu), followed by ASCII code
	// octets (67 for g, 6D for m, 75 for u). This is repeated for each label of the URL. The QNAME terminates with
	// the zero length octet for the null label of the root. Note that this field may be an odd number of octets; no
	// padding is used
	int count = 0;
	int index = 0;
	for (int i = 0; i < strlen(query_p->name); i++) {
		if (hostname[i] = '\0') {
			query_p->name[i + 1] = '0';
			break;
		}
		if (hostname[i] == '.') {
			query_p->name[index] = count + '0';
			index = i + 1;	
			count = 0;
			continue;
		}
		else {

		 /* Example:
		  *      +---+---+---+---+---+---+---+---+---+---+---+
		  *      | g | m | u | . | e | d | u |\0 |
		  *      +---+---+---+---+---+---+---+---+---+---+---+
		  *                     becomes:
		  *      +---+---+---+---+---+---+---+---+---+---+---+---+
		  *      | 3 | a | b | c | 3 | e | d | u | 0 |
		  *      +---+---+---+---+---+---+---+---+---+---+---+---+
		  */

			query_p->name[i + 1] = hostname[i]; 
			count++;
		}
	}
}

int* init_dns_request() {
	
}


