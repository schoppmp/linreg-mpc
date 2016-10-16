
#define _GNU_SOURCE // for asprintf

#include <gcrypt.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <zmq.h>

#include "check_error.h"
#include "fixed.h"
#include "test/test_multiplication.pb-c.h"


/*
  We are now using a PULL/PUSH.
  Each party pulls from its own public endpoint
  and pushes to the other parties endpoints.
  We might have synchronization problems if
  party 1 is faster than the initializer, as 
  party 2 might mistake sender.
  This will not happen once messages are authenticated.
*/

const int precision = 10;
const char *endpoint[3] = {
	"tcp://127.0.0.1:4567",
	"tcp://127.0.0.1:4568",
	"tcp://127.0.0.1:4569"
};

static int receive_value(fixed_t *value, void *sender) {
	int *val = sender;
  	printf("Receiving...\n");
	int status;
	check(value && sender, "receive_value: arguments may not be null");
	// receive message
	zmq_msg_t zmsg;
	status = zmq_msg_init(&zmsg);
	check(status == 0, "Could not initialize message: %s", zmq_strerror(errno));
	int len = zmq_msg_recv(&zmsg, sender, 0);
	check(len != -1, "Could not receive message: %s", zmq_strerror(errno));
	// unpack message
	Test__Fixed *pmsg = test__fixed__unpack(NULL, len, zmq_msg_data(&zmsg));
	check(pmsg != NULL, "Could not unpack message");
	*value = pmsg->value;

	printf("Received value %x\n", *value);

	// cleanup
	test__fixed__free_unpacked(pmsg, NULL);
	zmq_msg_close(&zmsg);
	return 0;

error:
	return -1;
}

static int send_value(fixed_t value, void *recipient) {
	int status;
	int *rec = recipient;
	printf("Sending value %x...", value);
	check(recipient, "send_value: recipient may not be null");
	// initialize message
	Test__Fixed pmsg;
	test__fixed__init(&pmsg);
	pmsg.value = value;
	zmq_msg_t zmsg;
	status = zmq_msg_init_size(&zmsg, test__fixed__get_packed_size(&pmsg));
	check(status == 0, "Could not initialize message: %s", zmq_strerror(errno));
	// pack payload and send
	test__fixed__pack(&pmsg, zmq_msg_data(&zmsg));
	status = zmq_msg_send(&zmsg, recipient, ZMQ_DONTWAIT); // asynchronous send
	check(status != -1, "Could not send message: %s", zmq_strerror(errno));
	printf("Done.\n");
	// cleanup
	zmq_msg_close(&zmsg);
	return 0;
error:
	return -1;
}

int main(int argc, char **argv) {
	void *socket[3] = {NULL, NULL, NULL};
	void *context = NULL;
	int status, retval = 1;

	check(argc >= 2, "Usage: %s Party [Input]", argv[0]);

	// parties are indexed starting with 1 to be 
	// consistent with notation in papers
	int party = 0;
	if(!strcmp(argv[1], "1")) {
		party = 1;
	} else if(!strcmp(argv[1], "2")) {
		party = 2;
	} else if(!strcmp(argv[1], "3")) {
		party = 3; // the trusted initializer (TI)
	}
	check(party > 0, "Party must be either 1, 2, or 3");

	// parties 1 and 2 provide inputs
	double input;
	if(party < 3) {
		check(argc >= 3, "Parties 1 and 2 need to provide an input");
		input = atof(argv[2]);
		check(errno == 0, "Invalid input: %s", strerror(errno));
	}

	// initialize zmq
	context = zmq_ctx_new();
	check(context, "Could not create context: %s", zmq_strerror(errno));
	// create and connect sockets
	for(int i = 0; i < 3; i++) {
		if(i == party - 1) { // create listen socket
		        socket[i] = zmq_socket(context, ZMQ_PULL);
			check(socket[i], "Could not create socket: %s", zmq_strerror(errno));
			status = zmq_bind(socket[i], endpoint[i]);
			check(status == 0, "Could not bind socket %s: %s", endpoint[i], zmq_strerror(errno));
			printf("Party %d pulling from %s\n", party, endpoint[i]);
			/* socket[i] = zmq_socket(context, ZMQ_REP); */
			/* check(socket[i], "Could not create socket: %s", zmq_strerror(errno)); */
			/* status = zmq_bind(socket[i], endpoint[i]); */
			/* check(status == 0, "Could not bind socket %s: %s", endpoint[i], zmq_strerror(errno)); */
		} else { // connect to the other parties
		        socket[i] = zmq_socket (context, ZMQ_PUSH);
			check(socket[i], "Could not create socket: %s", zmq_strerror(errno));
			zmq_connect(socket[i], endpoint[i]);
			check(status == 0, "Could not bind socket %s: %s", endpoint[i], zmq_strerror(errno));
			printf("Party %d pushing to %s\n", party, endpoint[i]);
			/* socket[i] = zmq_socket(context, ZMQ_REQ); */
			/* check(socket[i], "Could not create socket: %s", zmq_strerror(errno)); */
			/* status = zmq_connect(socket[i], endpoint[i]); */
			/* check(status == 0, "Could not connect to %s: %s", endpoint[i], zmq_strerror(errno)); */
		}
		//int linger = 0; // discard unsent messages when shutting down
		//zmq_setsockopt(socket[i], ZMQ_LINGER, &linger, sizeof(linger));
	}
	
	if(party == 3) { // Trusted Initializer
		// initialize libgcrypt for RNG
		check(gcry_check_version(GCRYPT_VERSION), "Unsupported gcrypt version");
		gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);
		// generate random masks and send them to parties 1 and 2
		fixed_t mask[2] = {0, 0};
		for(int i = 0; i < 2; i++) {
		        gcry_randomize(&mask[i], 4, GCRY_STRONG_RANDOM);
			printf("TI:: Sending message to party %d: %x\n", i+1, mask[i]);
			status = send_value(mask[i], socket[i]);
			check(status == 0, "Error sending message to party %d", i+1);
		}

		fixed_t share = mask[0]*mask[1];
		printf("Party %d:: Share: %x\n", party, share);

		// receive first share
		fixed_t share_1;
		status = receive_value(&share_1, socket[party - 1]);
		check(status == 0, "Error receiving message");

		// receive second share
		fixed_t share_2;
		status = receive_value(&share_2, socket[party - 1]);
		check(status == 0, "Error receiving message");


		fixed_t share_1_ = share_1 /  (1 << precision);
		fixed_t share_2_ = share_2 / (1 << precision);
		fixed_t share_ = share / (1 << precision);
		fixed_t share_1_rem = share_1 & ((1 << precision) - 1);
		fixed_t share_2_rem = share_2 & ((1 << precision) - 1);
		fixed_t share_rem = share & ((1 << precision) - 1);
		printf("Party %d:: Share 1: %d\n", party, share_1);
		printf("Party %d:: Share 1: %d\n", party, share_1_);
		printf("Party %d:: Share 1 remainder: %d\n", party, share_1_rem);
		printf("Party %d:: Share 2: %d\n", party, share_2);
		printf("Party %d:: Share 2: %d\n", party, share_2_);
		printf("Party %d:: Share 2 remainder: %d\n", party, share_2_rem);
		printf("Party %d:: Share 3: %d\n", party, share);
		printf("Party %d:: Share 3: %d\n", party, share_);
		printf("Party %d:: Share 3 remainder: %d\n", party, share_rem);
		printf("Party %d:: Result: %f\n", party, fixed_to_double(share_1+share_2+share, 2*precision));
		printf("Party %d:: Result: %f\n", party, fixed_to_double(share_1_+share_2_+share_, precision));
		printf("Party %d:: Result: %f\n", party, fixed_to_double(share_1_+share_2_+share_, precision) + fixed_to_double(share_1_rem+share_2_rem+share_rem, 2*precision));
		printf("Party %d:: Result (fixed): %d\n", party, share_1+share_2+share);
		printf("Party %d:: Result (fixed): %d\n", party, share_1_+share_2_+share_);

		
	} else {
		fixed_t a;
		fixed_t x = double_to_fixed(input, precision);
		printf("Party %d:: Input %f\n", party, input);
		printf("Party %d:: Input (fixed) %d\n", party, x);
		//printf("Party %d:: Input %f\n", party, fixed_to_double(x, precision));
		printf("Party %d:: Expecting value in socket %d\n", party, party-1);
		status = receive_value(&a, socket[party-1]);
		check(status == 0, "Error receiving message from TI");

		printf("Party %d:: value received: %x\n", party, a);

		if(party == 1){
		  	// send (x + a) to party 2
		        status = send_value(x + a, socket[party % 2]);
			check(status == 0, "Error sending message to party %d", party % 2 + 1);

			printf("Party %d:: Value sent to party %d: %x\n", party, party % 2 + 1, a);
		
			// receive value from party 2
			fixed_t a2;
			status = receive_value(&a2, socket[party - 1]);
			check(status == 0, "Error receiving message from party %d", party % 2 + 1);

			printf("a = %x\n", a);
			printf("a2 = %x\n", a2);
			printf("x = %d\n", x);
			
			fixed_t share = -(x + a)*a2+x*a2;
			printf("Party %d:: Share: %x\n", party, share);
			status = send_value(share, socket[2]);
			check(status == 0, "Error sending message");

		} else { // party == 2
		       // receive value from party 1
		       fixed_t a2;
		       status = receive_value(&a2, socket[party - 1]);
		       check(status == 0, "Error receiving message from party %d", party % 2 + 1);
		
		       // send (x + a) to party 1
		       status = send_value(x + a, socket[party % 2]);
		       check(status == 0, "Error sending message to party %d", party % 2 + 1);

		       printf("Party %d:: Value sent to party %d: %x\n", party, party % 2 + 1, a);

		       printf("a = %x\n", a);
		       printf("a2 = %x\n", a2);
		       printf("x = %d\n", x);
		       
		       fixed_t share = a2*x;
		       printf("Party %d:: Share: %x\n", party, share);
		       // send share to TI
		       status = send_value(share, socket[2]);
		       check(status == 0, "Error sending message");
		}
		
	}
		
	retval = 0;

error:
	for(int i = 0; i < 3; i++) {
		if(socket[i]) zmq_close(socket[i]);
	}
	if(context) zmq_ctx_destroy(context);
	return retval;
}
