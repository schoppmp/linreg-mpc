

#define _GNU_SOURCE

#include "error.h"
#include "test/test_multiplication.pb-c.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <zmq.h>


int main(int argc, char **argv) {
	char *endpoint[3] = {NULL, NULL, NULL};
	check(argc >= 5, "Usage: %s Party Address1 Address2 Address3 [Input]", argv[0]);

	int status;
	int party = 0;
	if(!strcmp(argv[1], "1")) {
		party = 1;
	} else if(!strcmp(argv[1], "2")) {
		party = 2;
	} else if(!strcmp(argv[1], "3")) {
		party = 3;
	}
	check(party > 0, "Party must be either 1, 2, or 3");

	double input;
	if(party < 3) {
		// parties 1 and 2 provide inputs
		check(argc >= 6, "Parties 1 and 2 need to provide an input");
		input = atof(argv[5]);
		check(errno == 0, "Invalid input: %s", strerror(errno));
	}

	for(int i = 0; i < 3; i++) {
		if(i == party - 1) {
			char *port = strchr(argv[i + 2], ':');
			check(port, "Address must be of the format host:port");
			status = asprintf(&(endpoint[i]), "tcp://*%s", port);
		} else {
			status = asprintf(&(endpoint[i]), "tcp://%s", argv[i + 2]);
		}
		check(status != -1, "%s", strerror(errno));
	}

	// initialise zmq and bind socket
	void *context = zmq_ctx_new();
	check(context, "Could not create context: %s", zmq_strerror(errno));
	void *responder = zmq_socket(context, ZMQ_REP);
	check(responder, "Could not create socket: %s", zmq_strerror(errno));
	status = zmq_bind(responder, endpoint[party - 1]);
	check(status == 0, "Could not bind socket: %s", zmq_strerror(errno));

	return 0;

error:
	for(int i = 0; i < 3; i++) {
		free(endpoint[i]);
	}
	return 1;
}
