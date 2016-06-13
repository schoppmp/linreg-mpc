#include <string.h>
#include <czmq.h>
#include <stdio.h>

#include "network.h"
#include "error.h"
#include "obliv.h"

typedef struct zsock_transport {
	ProtocolTransport cb;
	zsock_t *socket;
	// buffer for received data that was not read by oblivc yet
	char *buf;
	size_t start, len;
} zsock_transport_t;

static int protocol_zsock_send(ProtocolTransport *pt, int dest, const void *data, size_t n) {
	zsock_transport_t *trans = (zsock_transport_t *) pt;
	int status = zsock_send(trans->socket, "b", data, n);
	return status;
}

static int protocol_zsock_recv(ProtocolTransport *pt, int dest, void *data, size_t n) {
	zsock_transport_t *trans = (zsock_transport_t *) pt;
	size_t n2;
	while(n > n2) {
		size_t available = trans->len - trans->start;
		if(available > 0) { // copy data from last message
			size_t amount = n - n2 > available ? available : n - n2;
			memcpy(data + n2, trans->buf + trans->start, amount);
			trans->start += amount;
			n2 += amount;
			if(trans->start == trans->len) { // all data read -> clear buf
				free(trans->buf);
				trans->buf = NULL;
				trans->start = trans->len = 0;
			}
		} else { // buffer empty -> read a message
			int status = zsock_recv(trans->socket, "b", &trans->buf, &trans->len);
			check(status != -1, "%s", strerror(errno));
		}
	}

	return n2;
error:
	return -1;
}

static void protocol_zsock_cleanup(ProtocolTransport *pt) {
	zsock_transport_t *trans = (zsock_transport_t *) pt;
	free(trans->buf);
	free(trans);
	// do not free socket here but leave it for its creator
}
	

int protocol_use_zsock(ProtocolDesc *pd, zsock_t *socket) {
	zsock_transport_t *trans = malloc(sizeof(zsock_transport_t));
	*trans = (zsock_transport_t) {
		.cb = {
			.maxParties = 2, 
			.send = protocol_zsock_send, 
			.recv = protocol_zsock_recv, 
			.cleanup = protocol_zsock_cleanup
		},
		.socket = socket
	};

	pd->trans = &trans->cb;
	return 0;
}
