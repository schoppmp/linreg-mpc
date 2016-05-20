#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sodium.h>
#include <time.h>

#include "secure_multiplication/secure_multiplication.pb-c.h"
#include "secure_multiplication/secure_multiplication.h"
#include "secure_multiplication/node.h"
#include "secure_multiplication/config.h"
#include "check_error.h"
#include "linear.h"
#include "secure_multiplication/phase1.h"
#include "input.h"

static int barrier(node *self) {
	// wait until everybody is here
	for(int i = 0; i < self->num_peers; i++) {
		if(i == self->peer_id) continue;
		check(!zsock_signal(self->peer[i], 0), // value is arbitrary
			"zsock_signal: %s\n", zmq_strerror(errno));
	}
	for(int i = 0; i < self->num_peers; i++) {
		if(i == self->peer_id) continue;
		check(!zsock_wait(self->peer[i]),
			"zsock_signal: %s\n", zmq_strerror(errno));
	}
	return 0;

	error: return 1;
}

int main(int argc, char **argv) {
	uint32_t *share_A, *share_b; 
	config *c = NULL;
	node *self = NULL;
	int status;
	struct timespec cputime_start, cputime_end;
	struct timespec realtime_start, realtime_end;
	struct timespec wait_total;
	wait_total.tv_sec = wait_total.tv_nsec = 0;

	// parse arguments
	check(argc > 3, "Usage: %s file precision party", argv[0]);
	char *end;
	int precision = (int) strtol(argv[2], &end, 10);
	check(!errno, "strtol: %s", strerror(errno));
	check(!*end, "Precision must be a number");
	int party = (int) strtol(argv[3], &end, 10);
	check(!errno, "strtol: %s", strerror(errno));
	check(!*end, "Party must be a number");

	// read config
	status = config_new(&c, argv[1]);
	check(!status, "Could not read config");
	if(party == 1){
		c->party = party - 1;
	} else if(party == 2){
		c->party = -1;
	} else {
		c->party = party - 2;
	}

	if(party == 1) {
		printf("{\"n\":\"%zd\", \"d\":\"%zd\" \"p\":\"%d\"}\n", c->n, c->d, c->num_parties - 1);
	}

	status = node_new(&self, c);
	check(!status, "Could not create node");


	if(c->party == 0) {
		status = run_trusted_initializer(self, c);
		check(!status, "Error while running trusted initializer");
	} else if(c->party != -1){
		status = run_party(self, c, precision, &wait_total, &share_A, &share_b);
		check(!status, "Error while running party %d", c->party);
	}
	
	// wait until everybody has finished
	check(!barrier(self), "Error while waiting for other peers to finish");
	node_free(&self); // free the endpoints from 0MQ to be ued by Oblivc

	// At this point:
	// if party = 1 then I am the CSP and c->party = 0
	// if party = 2 then I am the Evaluator and c->party = -1
	// if party > 2 then 
	//   - I am a data provider and c->party = party - 2
    //   - share_A and share_b are my shares of the equation

	// Here phase 2 starts
	// We first setup the protocol description for CSP and Evaluator
	ProtocolDesc pd;
	char* csp_port = strchr(conf->endpoint[0], ':') + 1;
	*(csp_port - 1) = '\0'; // Removing whatever is after :
	char* csp_server = c->endpoints[0];
	char* eval_port = strchr(conf->endpoint_evaluator, ':') + 1;
	*(eval_port - 1) = '\0'; // Removing whatever is after :
	char* eval_server = c->endpoint_evaluator;
	if(party < 3){  // CSP and Evaluator
		ocTestUtilTcpOrDie(&pd, party==1, party==1 ? csp_port : eval_port);
		setCurrentParty(&pd, party);
		// Run garbled circuit
		// We'll modify linear.oc so that the inputs are read from a ls if the provided one is not NULL
		// else we'l use dcrRcvdIntArray...

	} else {
		DualconS* conn = dcsConnect(csp_server, csp_port, eval_server, eval_port, party);
		dcsSendIntArray(conn, share_A, d*(d + 1)/2);
		dcsSendIntArray(conn, share_b, d);
		dcsClose(conn);
	}
	
	config_free(&c);
	return 0;
error:
	config_free(&c);	
	node_free(&self);
	return 1;
}
