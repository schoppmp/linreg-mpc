#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

#include "secure_multiplication.pb-c.h"
#include "node.h"
#include "config.h"
#include "check_error.h"
#include "linear.h"
#include "phase1.h"
#include "obliv_common.h"

static int barrier(node *self) {
	// wait until everybody is here
	int flag = 42; // value is arbitrary
	if(self->party != 1) {
		check(orecv(self->peer[self->party-2], 0, &flag, sizeof(flag)) == sizeof(flag),
			"orecv: %s", strerror(errno));
	}
	if(self->party != self->num_parties) {
		check(osend(self->peer[self->party], 0, &flag, sizeof(flag)) == sizeof(flag),
			"osend: %s", strerror(errno));
		check(orecv(self->peer[self->party], 0, &flag, sizeof(flag)) == sizeof(flag),
			"orecv: %s", strerror(errno));
	}
	if(self->party != 1) {
		check(osend(self->peer[self->party-2], 0, &flag, sizeof(flag)) == sizeof(flag),
			"osend: %s", strerror(errno));
		orecv(self->peer[self->party-2],0,NULL,0);
	}
	return 0;

error:
	return -1;
}


int main(int argc, char **argv) {
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
	c->party = party;

	if(party == 1) {
		printf("{\"n\":\"%zd\", \"d\":\"%zd\", \"p\":\"%d\"}\n", c->n, c->d, c->num_parties-2);
	}

	status = node_new(&self, c);
	check(!status, "Could not create node");

	// wait until everybody has started up
	barrier(self);
	clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &cputime_start);
	clock_gettime(CLOCK_MONOTONIC, &realtime_start);

	if(c->party == 1) {
		status = run_trusted_initializer(self, c, precision);
		check(!status, "Error while running trusted initializer");
	} else if(c->party > 2) {
		status = run_party(self, c, precision, &wait_total, NULL, NULL);
		check(!status, "Error while running party %d", c->party);
	}


	clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &cputime_end);
	clock_gettime(CLOCK_MONOTONIC, &realtime_end);

	double bill = 1000000000L;
	printf("{\"party\":\"%d\", \"cputime\":\"%f\", \"wait_time\":%f, \"realtime\":\"%f\"}\n", c->party,
		(cputime_end.tv_sec - cputime_start.tv_sec) +
		(double) (cputime_end.tv_nsec - cputime_start.tv_nsec) / bill,
		(wait_total.tv_sec) +
		(double) (wait_total.tv_nsec) / bill,
		(realtime_end.tv_sec - realtime_start.tv_sec) +
		(double) (realtime_end.tv_nsec - realtime_start.tv_nsec) / bill);

	// wait until everybody has finished
	barrier(self);

	node_destroy(&self);
	config_destroy(&c);
	return 0;
error:
	config_destroy(&c);
	node_destroy(&self);
	return 1;
}
