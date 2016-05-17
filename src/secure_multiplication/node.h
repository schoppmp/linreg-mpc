#pragma once
#include <czmq.h>

#include "config.h"



typedef struct node {
	int peer_id;
	int num_peers;
	zsock_t **peer;

	// internal fields, not to be used by the application
	zactor_t *actor; // switches messages
	zsock_t *socket; // incoming router socket
	zsock_t **socket_out; // outgoing dealer socket for each peer
	char **endpoint;
	zsock_t **peer_handler; // internal socket
	zhashx_t *peer_map; // maps endpoints to peer_handlers
} node;

int node_new(node **n, config *conf);

void node_free(node **n);
