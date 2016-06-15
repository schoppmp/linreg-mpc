
#define _GNU_SOURCE // for asprintf

#include <gcrypt.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <zmq.h>

#include "check_error.h"
#include "fixed.h"
#include "linear.h"
#include "test/test_inner_product.pb-c.h"

#include <alloca.h>

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

static void random_vector_t(vector_t *vector){
	for(size_t i = 0; i < vector->len; i++) {
		gcry_randomize(&vector->value[i], sizeof(fixed64_t), GCRY_STRONG_RANDOM);
	}
}

static int receive_msg(vector_t *vector, fixed64_t *value, void *sender) {
	int *val = sender;
  	printf("Receiving msg...");
	int status;
	check(value && sender, "receive_value: arguments may not be null");
	// receive message
	zmq_msg_t zmsg;
	status = zmq_msg_init(&zmsg);
	check(status == 0, "Could not initialize message: %s", zmq_strerror(errno));
	int len = zmq_msg_recv(&zmsg, sender, 0);
	check(len != -1, "Could not receive message: %s", zmq_strerror(errno));
	// unpack message
	InnerProduct__Msg *pmsg = inner_product__msg__unpack(NULL, len, zmq_msg_data(&zmsg));
	check(pmsg != NULL, "Could not unpack message");
	*value = pmsg->value;
	//vector->value = pmsg->vector;
	vector->len = pmsg->n_vector;
	printf("Vector received: ");
	for(size_t i=0; i<vector->len; ++i){
		if(i==vector->len-1) printf("\n");
		vector->value[i] = pmsg->vector[i];
	}
	// cleanup
	inner_product__msg__free_unpacked(pmsg, NULL);
	zmq_msg_close(&zmsg);
	printf("Done.\n");
	return 0;

error:
	return -1;
}

static int send_msg(vector_t *vector, fixed64_t value, void *recipient) {
	int status;
	int *rec = recipient;
	printf("Sending msg...\n");
	printf("Vector being sent: ");
	for(size_t i=0; i<vector->len; ++i){
		printf("%x ", vector->value[i]);
		if(i==vector->len-1) printf("\n");
	}
	check(recipient, "send_value: recipient may not be null");
	// initialize message
	InnerProduct__Msg pmsg;
	inner_product__msg__init(&pmsg);
	pmsg.value = value;
	pmsg.vector = vector->value;
	pmsg.n_vector = vector->len;
	zmq_msg_t zmsg;
	status = zmq_msg_init_size(&zmsg, inner_product__msg__get_packed_size(&pmsg));
	check(status == 0, "Could not initialize message: %s", zmq_strerror(errno));
	// pack payload and send
	inner_product__msg__pack(&pmsg, zmq_msg_data(&zmsg));
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

	check(argc >= 2, "Usage: %s party_num d input[0] ... input[d-1]", argv[0]);

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
	double *input;
	int d = 0;
	d = atoi(argv[2]);
	check(d > 0, "dimension must be greater than 0");
	if(party < 3) {
		check(argc >= 3, "Parties 1 and 2 need to provide an input");
		check(errno == 0, "Invalid input: %s", strerror(errno));
		input = malloc(d * sizeof(double));
		for(int i = 0; i < d; i++){
			input[i] = atof(argv[3 + i]);
		}
	}

	printf("Party %d:: d = %x\n", party, d);

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
		} else { // connect to the other parties
	        socket[i] = zmq_socket (context, ZMQ_PUSH);
			check(socket[i], "Could not create socket: %s", zmq_strerror(errno));
			zmq_connect(socket[i], endpoint[i]);
			check(status == 0, "Could not bind socket %s: %s", endpoint[i], zmq_strerror(errno));
			printf("Party %d pushing to %s\n", party, endpoint[i]);
		}
	}

	if(party == 3) { // Trusted Initializer
		// initialize libgcrypt for RNG
		check(gcry_check_version(GCRYPT_VERSION), "Unsupported gcrypt version");
		gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);
		// generate random vectors x,y and random number r
		vector_t x;
		x.len = d;
		x.value = malloc(d * sizeof(fixed64_t));
		random_vector_t(&x);
		vector_t y;
		y.len = d;
		y.value = malloc(d * sizeof(fixed64_t));
		random_vector_t(&y);
		fixed64_t r = 0;
		gcry_randomize(&r, sizeof(r), GCRY_STRONG_RANDOM);
		printf("Party %d:: r = %x\n", party, r);
		printf("Party %d:: x = ", party);
		for(size_t i=0; i<x.len; ++i){
			printf("%x ", x.value[i]);
			if(i==x.len-1) printf("\n");
		}
		printf("Party %d:: y = ", party);
		for(size_t i=0; i<y.len; ++i){
			printf("%x ", y.value[i]);
			if(i==x.len-1) printf("\n");	
		}
		// send (x,r) to party 1
		printf("TI:: Sending message to party %d\n", 1);
		status = send_msg(&x, r, socket[0]);
		check(status == 0, "Error sending message to party %d", 1);
		// send (y, <x, y> -r) to party 2
		printf("TI:: Sending vector to party %d\n", 2);
		status = send_msg(&y, inner_product(&x, &y) - r, socket[1]);
		check(status == 0, "Error sending message to party %d", 2);

		// this is for testing purposes
		// receive first share
		vector_t dummy_vector;
		fixed64_t share_1;
		status = receive_msg(&dummy_vector, &share_1, socket[party - 1]);
		check(status == 0, "Error receiving message");

		// receive second share
		fixed64_t share_2;
		status = receive_msg(&dummy_vector, &share_2, socket[party - 1]);
		check(status == 0, "Error receiving message");

		printf("Party %d:: Result: %f\n", party, fixed_to_double(share_1+share_2, 2*precision));
				
	} else {
		vector_t input_fixed;
		input_fixed.len = d;
		input_fixed.value = malloc(d * sizeof(fixed64_t));
		for(size_t i=0; i<input_fixed.len; ++i){
			input_fixed.value[i] = double_to_fixed(input[i], precision);
		}
		printf("Party %d:: Input = ", party);
		for(size_t i=0; i<d; ++i){
			printf("%f ", input[i]);
			if(i == d - 1) printf("\n");	
		}
		printf("Party %d:: Input(fixed) = ", party);
		for(size_t i=0; i<d; ++i){
			printf("%x ", input_fixed.value[i]);
			if(i == d - 1) printf("\n");	
		}
		printf("Party %d:: Expecting value in socket %d\n", party, party-1);
		vector_t in_vector_1;
		in_vector_1.len = d;
		in_vector_1.value = malloc(d * sizeof(fixed64_t));
		fixed64_t in_value_1;
		status = receive_msg(&in_vector_1, &in_value_1, socket[party-1]);
		check(status == 0, "Error receiving message from TI");
		printf("Party %d:: msg received\n", party);
		printf("Party %d:: vector received = ", party);
		for(size_t i=0; i<d; ++i){
			printf("%x ", in_vector_1.value[i]);
			if(i == d - 1) printf("\n");	
		}
		if(party == 2){
		  	// send (b - y) to party 1
		  	vector_t out_vector;
		  	out_vector.len = d;
			out_vector.value = malloc(d * sizeof(fixed64_t));
			for(size_t i=0; i<input_fixed.len; ++i){
				out_vector.value[i] = input_fixed.value[i] - in_vector_1.value[i];
			}
		    status = send_msg(&out_vector, 0, socket[0]);
			check(status == 0, "Error sending message to party %d", 1);
			printf("Party %d:: Msg sent to party %d", party, 1);
		
			// receive msg from party 1
			vector_t in_vector_2;
			in_vector_2.len = d;
			in_vector_2.value = malloc(d * sizeof(fixed64_t));
			fixed64_t in_value_2;
			status = receive_msg(&in_vector_2, &in_value_2, socket[party-1]);
			check(status == 0, "Error receiving messages from party %d", 1);

			fixed64_t share = inner_product(&in_vector_2, &in_vector_1) + in_value_2 - in_value_1;
			printf("Party %d:: Share: %x\n", party, share);
			// send share to TI (this is for testing purposes)
			vector_t dummy_vector;
			dummy_vector.len = 0;
			status = send_msg(&dummy_vector, share, socket[2]);
			check(status == 0, "Error sending message");

		} else { // party == 1
			// receive (b -y, _) from party 2
			vector_t in_vector_2;
			in_vector_2.len = d;
			in_vector_2.value = malloc(d * sizeof(fixed64_t));
			fixed64_t in_value_2;
			status = receive_msg(&in_vector_2, &in_value_2, socket[party-1]);
			check(status == 0, "Error receiving message from party %d", 2);

			// generate random number u
			fixed64_t u = 0;
			gcry_randomize(&u, sizeof(u), GCRY_STRONG_RANDOM);

			// Send (a + x, <a, b - y> -u) to party 2
			vector_t out_vector;
		  	out_vector.len = d;
			out_vector.value = malloc(d * sizeof(fixed64_t));
			for(size_t i=0; i<input_fixed.len; ++i){
				out_vector.value[i] = input_fixed.value[i] + in_vector_1.value[i];
			}
		    status = send_msg(&out_vector, inner_product(&input_fixed, &in_vector_2) - u, socket[1]);
			check(status == 0, "Error sending message to party %d", 2);
			printf("Party %d:: Msg sent to party %d\n", party, 2);

			fixed64_t share = u - in_value_1;
			printf("Party %d:: Share: %x\n", party, share);
		    // send share to TI (this is for testing purposes)
		    vector_t dummy_vector; 
		    dummy_vector.len = 0;
			status = send_msg(&dummy_vector, share, socket[2]);
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
