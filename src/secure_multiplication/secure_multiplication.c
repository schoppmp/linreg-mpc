#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sodium.h>

#include "secure_multiplication.pb-c.h"
#include "secure_multiplication.h"
#include "node.h"
#include "config.h"
#include "error.h"
#include "linear.h"


static int get_owner(int row, config *conf) {
	check(row < conf->d, "Invalid row %d", row);
	int party = 0;
	for(;party + 1 < conf->num_parties && conf->index_owned[party+1] <= row; party++);
	return party;

error:
	return -1;
}


static int run_trusted_initializer(node *self, config *c) {
	int status;
	for(size_t i = 0; i < c->d; i++) {
		for(size_t j = 0; j <= i; j++) {
			//SecureMultiplication__Msg msg;
			//secure_multiplication__msg__init(&msg);
			// generate random vectors x, y and value r
			uint32_t *x = malloc(c->n * sizeof(uint32_t));
			check(x, "malloc: %s", strerror(errno));
			uint32_t *y = malloc(c->n * sizeof(uint32_t));
			check(x, "malloc: %s", strerror(errno));
			uint32_t xy = 0, r;
			randombytes_buf(x, c->n * sizeof(uint32_t));
			randombytes_buf(y, c->n * sizeof(uint32_t));
			randombytes_buf(&r, sizeof(uint32_t));
			// compute inner product of x, y
			for(size_t k = 0; k < c->n; k++) {
				xy += x[k] * y[k];
			}

			// get parties a and b
			int party_a = get_owner(i, c), party_b = get_owner(j, c);
			check(party_a > 0 && party_b > 0, "Invalid index (%d, %d)", i, j);

			// create protobuf message
			SecureMultiplication__Msg pmsg_a, pmsg_b;
			secure_multiplication__msg__init(&pmsg_a);
			secure_multiplication__msg__init(&pmsg_b);
			pmsg_a.vector = x;
			pmsg_a.value = r;
			pmsg_b.vector = y;
			pmsg_b.value = xy-r;

			// create czmq frames
			zframe_t *zframe_a = zframe_new(NULL, secure_multiplication__msg__get_packed_size(&pmsg_a));
			zframe_t *zframe_b = zframe_new(NULL, secure_multiplication__msg__get_packed_size(&pmsg_b));
			check(zframe_a && zframe_b, "zframe_new: %s", zmq_strerror(errno));

			// pack and send frames
			secure_multiplication__msg__pack(&pmsg_a, zframe_data(zframe_a));
			secure_multiplication__msg__pack(&pmsg_b, zframe_data(zframe_a));
			zframe_send(&zframe_a, self->peer[party_a], 0);
			zframe_send(&zframe_b, self->peer[party_b], 0);
		}
	}
	return 0;

error:
	return 1;
}


static int run_party(node *self, config *c) {
	for(int i = 0; i < c->d; i++) {
		for(int j = 0; j <= i; j++) {
			
		}
	}
	usleep(200000);
	return 0;

error:
	return 1;
}


int main(int argc, char **argv) {
	config *c = NULL;
	node *self = NULL;
	int status;

	// parse arguments
	check(argc > 2, "Usage: %s file party", argv[0]);
	char *end;
	int party = (int) strtol(argv[2], &end, 10);
	check(!errno, "strtol: %s", strerror(errno));
	check(!*end, "Party must be a number");

	// read config
	status = config_new(&c, argv[1]);
	check(!status, "Could not read config");
	c->party = party;

	status = node_new(&self, c);
	check(!status, "Could not create node");

	if(c->party == 0) {
		status = run_trusted_initializer(self, c);
		check(!status, "Error while running trusted initializer");
	} else {
		status = run_party(self, c);
		check(!status, "Error while running party %d", c->party);
	}

	node_free(&self);
	config_free(&c);
	return 0;
error:
	config_free(&c);	
	node_free(&self);
	return 1;
}
