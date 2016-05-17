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

const int precision = 24;

// computes inner product in Z_{2^32}
static uint32_t inner_prod_32(uint32_t *x, uint32_t *y, size_t n, size_t stride_x, size_t stride_y) {
	uint32_t xy = 0;
	for(size_t i = 0; i < n; i++) {
		xy += x[i*stride_x] * y[i*stride_y];
	}
	return xy;
}


// returns the party who owns a certain row
// the target vector with the hightes index is owned by the last party
static int get_owner(int row, config *conf) {
	check(row <= conf->d, "Invalid row %d", row);
	int party = 0;
	for(;party + 1 < conf->num_parties && conf->index_owned[party+1] <= row; party++);
	return party;

error:
	return -1;
}

// receives a message from peer, storing it in pmsg
// the result should be freed by the caller after use
static int recv_pmsg(SecureMultiplication__Msg **pmsg, zsock_t *peer) {
	//static int count = 0;
	//printf("received: %d\n", ++count);
	zframe_t *zframe = NULL;
	check(pmsg && peer, "recv_pmsg: Arguments may not be null");
	*pmsg = NULL;

	zframe = zframe_recv(peer);
	check(zframe, "zframe_recv: %s", zmq_strerror(errno));
	//zframe_print(zframe, "recvd: ");
	*pmsg = secure_multiplication__msg__unpack(NULL, zframe_size(zframe), zframe_data(zframe));
	check(*pmsg && (*pmsg)->vector, "msg__unpack: %s", strerror(errno));

	zframe_destroy(&zframe);
	return 0;
error:
	if(zframe) zframe_destroy(&zframe);
	return 1;			
}

// sends the message pointed to by pmsg to peer
static int send_pmsg(SecureMultiplication__Msg *pmsg, zsock_t *peer) {
	//static int count = 0;
	//printf("sent: %d\n", ++count);
	zframe_t *zframe = NULL;
	check(pmsg && peer, "send_pmsg: Arguments may not be null");

	zframe = zframe_new(NULL, secure_multiplication__msg__get_packed_size(pmsg));
	check(zframe, "zframe_new: %s", zmq_strerror(errno));
	// pack and send frames
	secure_multiplication__msg__pack(pmsg, zframe_data(zframe));
	//zframe_print(zframe, "sending: ");
	check(zframe_send(&zframe, peer, 0) != -1, "zframe_send: %s", zmq_strerror(errno));
	return 0;
error:
	if(zframe) zframe_destroy(&zframe);
	return 1;
}


static int run_trusted_initializer(node *self, config *c) {
	int status;
	uint32_t *x = malloc(c->n * sizeof(uint32_t));
	uint32_t *y = malloc(c->n * sizeof(uint32_t));
	check(x && y, "malloc: %s", strerror(errno));
	for(size_t i = 0; i <= c->d; i++) {
		for(size_t j = 0; j <= i && j < c->d; j++) {
			// get parties a and b
			int party_a = get_owner(i, c);
			int party_b = get_owner(j, c);
			// if parties are identical, skip; will be computed locally
			if(party_a == party_b) {
				continue;
			}

			// generate random vectors x, y and value r
			uint32_t r;
			randombytes_buf(x, c->n * sizeof(uint32_t));
			randombytes_buf(y, c->n * sizeof(uint32_t));
			randombytes_buf(&r, sizeof(uint32_t));
			uint32_t xy = inner_prod_32(x, y, c->n, 1, 1);

			// create protobuf message
			SecureMultiplication__Msg pmsg_a, pmsg_b;
			secure_multiplication__msg__init(&pmsg_a);
			secure_multiplication__msg__init(&pmsg_b);
			pmsg_a.vector = x;
			pmsg_a.n_vector = c->n;
			pmsg_a.value = r;
			pmsg_b.vector = y;
			pmsg_b.n_vector = c->n;
			pmsg_b.value = xy-r;

			printf("%d -> %d\n", c->party, party_a);
			status = send_pmsg(&pmsg_a, self->peer[party_a]);
			check(!status, "Could not send message to party A (%d)", party_a);
			printf("%d -> %d\n", c->party, party_b);
			status = send_pmsg(&pmsg_b, self->peer[party_b]);
			check(!status, "Could not send message to party B (%d)", party_b);
		}
	}
	free(x);
	free(y);
	return 0;

error:
	free(x);
	free(y);
	return 1;
}


static int run_party(node *self, config *c) {
//	sleep(1);
	matrix_t data; // TODO: maybe use dedicated type for finite field matrices here
	vector_t target;
	int status;
	SecureMultiplication__Msg *pmsg_ti = NULL, 
				  *pmsg_in = NULL,
				  pmsg_out;
	secure_multiplication__msg__init(&pmsg_out);
	pmsg_out.n_vector = c->n;
	pmsg_out.vector = malloc(c->n * sizeof(uint32_t));
	uint32_t *share_A = NULL, *share_b = NULL;
	check(pmsg_out.vector, "malloc: %s", strerror(errno));

	// read inputs and allocate result buffer
	status = read_matrix(c->input, &data, precision);
	check(!status, "Could not read data");
	status = read_vector(c->input, &target, precision);
	check(!status, "Could not read target");
	size_t d = data.d[1];
	check(c->n == target.len && d == c->d && c->n == data.d[0],
		"Input dimensions invalid: (%zd, %zd), %zd",
		data.d[0], data.d[1], target.len);
	share_A = calloc(d * (d + 1) / 2, sizeof(uint32_t));
	share_b = calloc(d, sizeof(uint32_t));

	for(int i = 0; i <= c->d; i++) {
		uint32_t *row_start;
		size_t stride;
		if(i < c->d) { // row of input matrix
			row_start = (uint32_t *) data.value + i;
			stride = d;
		} else { // row is target vector
			row_start = (uint32_t *) target.value;
			stride = 1;
		}
		for(int j = 0; j <= i && j < c->d; j++) {
			int owner_i = get_owner(i, c);
			int owner_j = get_owner(j, c);

			uint32_t share;
			// if we own neither i or j, skip.
			if(owner_i != c->party && owner_j != c->party) { 
				continue;
			// if we own both, compute locally
			} else if(owner_i == c->party && owner_i == owner_j) {
				share = inner_prod_32(row_start, (uint32_t *) data.value + j, c->n, stride, d);
			} else {
				// receive random values from TI
				printf("%d <- %d\n", c->party, 0);
				status = recv_pmsg(&pmsg_ti, self->peer[0]);
				check(!status, "Could not receive message from TI; %d %d", i, j);

				if(owner_i == c->party) { // if we own i but not j, we are party a
					// set our own share r_A randomly
					randombytes_buf(&share, sizeof(uint32_t));
					// receive (b', _) from party b
					int party_b = get_owner(j, c);

					printf("%d <- %d\n", c->party, party_b);
					status = recv_pmsg(&pmsg_in, self->peer[party_b]);
					check(!status, "Could not receive message from party B (%d)", party_b);

					// Send (a + x, <a, b'> - r - r_A) to party b
					pmsg_out.value = inner_prod_32(row_start, pmsg_in->vector, c->n, stride, 1)
						- pmsg_ti->value - share;
					for(size_t k = 0; k < c->n; k++) {
						pmsg_out.vector[k] = pmsg_in->vector[k] + pmsg_ti->vector[k];
					}
					printf("%d -> %d\n", c->party, party_b);
					status = send_pmsg(&pmsg_out, self->peer[party_b]);
					check(!status, "Could not send message to party B (%d)", party_b);

				} else { // if we own j but not i, we are party b
					int party_a = get_owner(i, c);
					// send (b - y, _) to party a
					pmsg_out.value = 0;
					for(size_t k = 0; k < c->n; k++) {
						//printf("%x %zd %zd %zd\n", pmsg_ti, i, j, k);
						pmsg_out.vector[k] = data.value[k * d + j] - pmsg_ti->vector[k];
					}

					printf("%d -> %d\n", c->party, party_a);
					status = send_pmsg(&pmsg_out, self->peer[party_a]);
					check(!status, "Could not send message to party A (%d)", party_a);
					
					// receive (a', a'') from party a
					printf("%d <- %d\n", c->party, party_a);
					status = recv_pmsg(&pmsg_in, self->peer[party_a]);
					check(!status, "Could not receive message from party A (%d)", party_a);

					// set our share to <a', y> + a'' - z
					share = inner_prod_32(pmsg_in->vector, pmsg_ti->vector, c-> n, 1, 1) 
						+ pmsg_in->value - pmsg_ti->value;
			
				}
				secure_multiplication__msg__free_unpacked(pmsg_in, NULL);
				secure_multiplication__msg__free_unpacked(pmsg_ti, NULL);
				pmsg_ti = pmsg_in = NULL;
			}
			// save our share
			if(i < c->d) {
				share_A[idx(i, j)] = share;
			} else {
				share_b[j] = share;
			}
		}
	}
	return 0;

error:
	free(pmsg_out.vector);
	free(share_A);
	free(share_b);
	if(pmsg_ti) secure_multiplication__msg__free_unpacked(pmsg_ti, NULL);
	if(pmsg_in) secure_multiplication__msg__free_unpacked(pmsg_in, NULL);
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
