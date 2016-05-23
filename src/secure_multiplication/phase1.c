#include "phase1.h"
#include <math.h>

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


int run_trusted_initializer(node *self, config *c) {
	int status;
	uint32_t *x = calloc(c->n , sizeof(uint32_t));
	uint32_t *y = calloc(c->n , sizeof(uint32_t));
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
			uint32_t r = 0;
			randombytes_buf(x, c->n * sizeof(uint32_t));
			for(size_t k = 0; k < c->n; k++) {
				y[k] = 1;
			}
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
			//assert(pmsg_b.value == 0);

			status = send_pmsg(&pmsg_a, self->peer[party_a]);
			check(!status, "Could not send message to party A (%d)", party_a);
			status = send_pmsg(&pmsg_b, self->peer[party_b]);
			check(!status, "Could not send message to party B (%d)", party_b);
		}
	}

/*	// Receive and combine shares from peers for testing; TODO: remove
	uint32_t *share_A = NULL, *share_b = NULL;
	size_t d = c->d;
	share_A = calloc(d * (d + 1) / 2, sizeof(uint32_t));
	share_b = calloc(d, sizeof(uint32_t));

	SecureMultiplication__Msg *pmsg_in;
	for(int p = 1; p < c->num_parties; p++) {
		status = recv_pmsg(&pmsg_in, self->peer[p]);
		check(!status, "Could not receive result share_A from peer %d", p);
		for(size_t i = 0; i < d * (d + 1) / 2; i++) {
			share_A[i] += pmsg_in->vector[i];
		}
		secure_multiplication__msg__free_unpacked(pmsg_in, NULL);
		status = recv_pmsg(&pmsg_in, self->peer[p]);
		check(!status, "Could not receive result share_b from peer %d", p);
		for(size_t i = 0; i < d; i++) {
			share_b[i] += pmsg_in->vector[i];
		}
		secure_multiplication__msg__free_unpacked(pmsg_in, NULL);
		
	}
	for(size_t i = 0; i < c->d; i++) {
		for(size_t j = 0; j <= i; j++) {
			printf("%f ", fixed_to_double((fixed32_t) share_A[idx(i, j)], precision));
		}
		printf("\n");
	}
*/
	free(x);
	free(y);
	return 0;

error:
	free(x);
	free(y);
	return 1;
}


int run_party(node *self, config *c, int precision, struct timespec *wait_total, uint32_t **res_A, uint32_t **res_b) {
	matrix_t data; // TODO: maybe use dedicated type for finite field matrices here
	vector_t target;
	data.value = target.value = NULL;
	int status;
	struct timespec wait_start, wait_end; // count how long we wait for other parties
	if(wait_total) {
		wait_total->tv_sec = wait_total->tv_nsec = 0;
	}
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

	
	for(size_t i = 0; i < c->n; i++) {
		for(size_t j = 0; j < c->d; j++) {
			// rescale in advance 
			data.value[i*c->d+j] = (fixed32_t) round(data.value[i*c->d+j] / (sqrt((1<<precision) * c->d * c->n)));
		}
		target.value[i] = (fixed32_t) round(target.value[i] / (sqrt((1<<precision) * c->d * c->n)));
	}

	for(size_t i = 0; i <= c->d; i++) {
		uint32_t *row_start;
		size_t stride;
		if(i < c->d) { // row of input matrix
			row_start = (uint32_t *) data.value + i;
			stride = d;
		} else { // row is target vector
			row_start = (uint32_t *) target.value;
			stride = 1;
		}
		for(size_t j = 0; j <= i && j < c->d; j++) {
			int owner_i = get_owner(i, c);
			int owner_j = get_owner(j, c);

			uint32_t share;
			// if we own neither i or j, skip.
			if(owner_i != c->party && owner_j != c->party) { 
				continue;
			// if we own both, compute locally
			} else if(owner_i == c->party && owner_i == owner_j) {
				share = inner_prod_32(row_start, (uint32_t *) data.value + j, 
					c->n, stride, d);
			} else {
				// receive random values from TI
				status = recv_pmsg(&pmsg_ti, self->peer[0]);
				check(!status, "Could not receive message from TI; %d %d", i, j);

				if(owner_i == c->party) { // if we own i but not j, we are party a
					// set our own share r_A randomly
					share = 0;
					randombytes_buf(&share, sizeof(uint32_t));
					// receive (b', _) from party b
					int party_b = get_owner(j, c);

					
					clock_gettime(CLOCK_MONOTONIC, &wait_start);
					status = recv_pmsg(&pmsg_in, self->peer[party_b]);
					clock_gettime(CLOCK_MONOTONIC, &wait_end);
					if(wait_total) {
						wait_total->tv_sec += (wait_end.tv_sec - wait_start.tv_sec);
						wait_total->tv_nsec += (wait_end.tv_nsec - wait_start.tv_nsec);
					}
					check(!status, "Could not receive message from party "
						"B (%d)", party_b);

					// Send (a + x, <a, b'> - r - r_A) to party b
					pmsg_out.value = inner_prod_32(row_start, pmsg_in->vector,
						c->n, stride, 1);
					pmsg_out.value -= (pmsg_ti->value + share);
					for(size_t k = 0; k < c->n; k++) {
						pmsg_out.vector[k] = row_start[k*stride] 
							+ pmsg_ti->vector[k];
					}
					status = send_pmsg(&pmsg_out, self->peer[party_b]);
					check(!status, "Could not send message to party B (%d)",
						party_b);

				} else { // if we own j but not i, we are party b
					int party_a = get_owner(i, c);
					// send (b - y, _) to party a
					pmsg_out.value = 0;
					for(size_t k = 0; k < c->n; k++) {
						pmsg_out.vector[k] = ((uint32_t *) data.value)[k * d + j]
							- pmsg_ti->vector[k];
						//assert(pmsg_out.vector[k] == 1023);
					}

					status = send_pmsg(&pmsg_out, self->peer[party_a]);
					check(!status, "Could not send message to party A (%d)",
						party_a);
					
					// receive (a', a'') from party a
					clock_gettime(CLOCK_MONOTONIC, &wait_start);
					status = recv_pmsg(&pmsg_in, self->peer[party_a]);
					clock_gettime(CLOCK_MONOTONIC, &wait_end);
					if(wait_total) {
						wait_total->tv_sec += (wait_end.tv_sec - wait_start.tv_sec);
						wait_total->tv_nsec += (wait_end.tv_nsec - wait_start.tv_nsec);
					}
					check(!status, "Could not receive message from party A (%d)", party_a);

					// set our share to <a', y> + a'' - z
					share = inner_prod_32(pmsg_in->vector, pmsg_ti->vector, c->n, 1, 1);
					share += pmsg_in->value - pmsg_ti->value;
			
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

	if(res_A){
		*res_A = share_A;
	} else {
		free(share_A);
	}
	if(res_b){
		*res_b = share_b;
	} else {
		free(share_b);
	}
	
	free(pmsg_out.vector);
/*	// send results to TI for testing; TODO: remove
	pmsg_out.vector = share_A;
	pmsg_out.n_vector = d * (d + 1) / 2;
	status = send_pmsg(&pmsg_out, self->peer[0]);
	check(!status, "Could not send share_A to TI");
	pmsg_out.vector = share_b;
	pmsg_out.n_vector = d;
	status = send_pmsg(&pmsg_out, self->peer[0]);
	check(!status, "Could not send share_b to TI");
*/
	free(data.value);
	free(target.value);
	return 0;

error:
	free(data.value);
	free(target.value);
	free(pmsg_out.vector);
	if(res_A){
		*res_A = NULL;
	} else {
		free(share_A);
	}
	if(res_b){
		*res_b = NULL;
	} else {
		free(share_b);
	}
	if(pmsg_ti) secure_multiplication__msg__free_unpacked(pmsg_ti, NULL);
	if(pmsg_in) secure_multiplication__msg__free_unpacked(pmsg_in, NULL);
	return 1;
}
