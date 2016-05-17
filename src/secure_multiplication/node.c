#include <czmq.h>
#include "node.h"
#include "error.h"

#define ACTOR_START 11
#define ACTOR_STOP 13
#define ACTOR_ERROR 17
#define ACTOR_OK 0

// switches messages between outgoing socket and internal sockets.
static void node_actor(zsock_t *pipe, void *nn) {
	node *self = (node *) nn;
	int status;
	char *sender = NULL;
	zmsg_t *msg = NULL;
	zmq_pollitem_t *pollitems = NULL;

	// listen for messages to send on each internal socket
	pollitems = calloc(self->num_peers + 2, sizeof(zmq_pollitem_t));
	for(int i = 0; i < self->num_peers; i++) {
		pollitems[i].socket = zsock_resolve(self->peer_handler[i]);
		check(pollitems[i].socket, "Could not resolve internal socket %i", i);
		pollitems[i].events = ZMQ_POLLIN;
	}
	// listen for incoming messages on our external socket
	pollitems[self->num_peers].socket = zsock_resolve(self->socket);
	check(pollitems[self->num_peers].socket, "Could not resolve external socket");
	pollitems[self->num_peers].events = ZMQ_POLLIN;
	// listen to pipe for commands from the application
	pollitems[self->num_peers+1].socket = zsock_resolve(pipe);
	check(pollitems[self->num_peers+1].socket, "Could not resolve actor pipe");
	pollitems[self->num_peers+1].events = ZMQ_POLLIN;

	// tell actor constructor we're finished initializing
	status = zsock_signal(pipe, ACTOR_OK);

	for(;;) { // receive messages forever
		// wait until at least one message is ready
		status = zmq_poll(pollitems, self->num_peers + 2, 1000);
		for(int i = 0; i < self->num_peers + 2; i++) {
			if(pollitems[i].revents != ZMQ_POLLIN) continue; // only receive available messages
			msg = zmsg_recv(pollitems[i].socket);
			check(msg, "zmsg_recv: %s", zmq_strerror(errno));
			if(i == self->num_peers) { // message came from outside
				// find out sender and route to appropriate internal socket
				sender = zmsg_popstr(msg);
				check(sender, "zmsg_popstr: %s", zmq_strerror(errno));
				zsock_t *peer_handler = (zsock_t *) zhashx_lookup(self->peer_map, sender);
				check(peer_handler, "zhashx_lookup: %s", zmq_strerror(errno));

				/*int count = 0;
				for(zframe_t *f = zmsg_first(msg); f != NULL; f = zmsg_next(msg)) {count++;}
				printf("Party %d received message from %s, containing %d frames.\n", self->peer_id, sender, count );
				zmsg_print(msg);*/

				status = zmsg_send(&msg, peer_handler);
				check(!status, "zmsg_send: %s", zmq_strerror(errno));
				free(sender);
				sender = NULL;
			} else if(i < self->num_peers) { // message came from the inside
				/*int count = 0;
				for(zframe_t *f = zmsg_first(msg); f != NULL; f = zmsg_next(msg)) {count++;}
				printf("Party %d sending message to %d, containing %d frames.\n", self->peer_id, i, count );
				zmsg_print(msg);*/

				status = zmsg_pushstr(msg, self->endpoint[i]);
				check(!status, "zmsg_pushstr: %s", zmq_strerror(errno));
				status = zmsg_send(&msg, self->socket);
				check(!status, "zmsg_send: %s", zmq_strerror(errno));
			} else { // control socket -> exit
				zmsg_destroy(&msg);
				free(pollitems);
				return;
			}
		}
	}


error:
	zsock_signal(pipe, ACTOR_ERROR);
	if(msg) zmsg_destroy(&msg);
	free(sender);
	free(pollitems);
	return;
}


// destructor for hash map
void node_destroy_socket(void **arg) {
	zsock_t *sock = (zsock_t *) *arg;
	zsock_destroy(&sock);
}


int node_new(node **nn, config *conf) {
	int status;
	check(nn && conf, "new_node: Arguments may not be null");

	// create objects
	*nn = calloc(1, sizeof(node));
	check(*nn, "calloc: %s", strerror(errno));
	node *self = *nn;
	
	self->endpoint = conf->endpoint;
	self->num_peers = conf->num_parties;
	self->peer_id = conf->party;

	self->peer_map = zhashx_new();
	check(self->peer_map, "zhashx_new: %s", zmq_strerror(errno));
	// destroy internal sockets automatically
	zhashx_set_destructor(self->peer_map, node_destroy_socket);

	// create sockets to be used by the application
	self->peer = calloc(self->num_peers, sizeof(zsock_t *));
	check(self->peer, "calloc: %s", strerror(errno));
	self->peer_handler = calloc(self->num_peers, sizeof(zsock_t *));
	check(self->peer_handler, "calloc: %s", strerror(errno));
	for(int i = 0; i < self->num_peers; i++) {
		zsock_t *peer = zsock_new(ZMQ_PAIR);
		check(peer, "zsock_new: %s", zmq_strerror(errno));
		self->peer[i] = peer;
		status = zsock_bind(peer, "inproc://%x", i);
		check(status != -1, "zsock_bind: %s", zmq_strerror(errno));
		// create corresponding internal socket
		zsock_t *peer_handler = zsock_new(ZMQ_PAIR);
		check(peer_handler, "zsock_new: %s", zmq_strerror(errno));
		self->peer_handler[i] = peer_handler;
		status = zsock_connect(peer_handler, "inproc://%x", i);
		check(status != -1, "zsock_connect: %s", zmq_strerror(errno));
		// insert internal socket into peer_map
		status = zhashx_insert(self->peer_map, self->endpoint[i], peer_handler);
		check(!status, "zhashx_insert: %s", zmq_strerror(errno));
	}

	self->socket = zsock_new(ZMQ_ROUTER);
	check(self->socket, "zsock_new: %s", zmq_strerror(errno));
	// report errors when trying to sent messages without address
	zsock_set_router_mandatory(self->socket, 1);
	// send empty message to all peers
	zsock_set_probe_router(self->socket, 1);
	// create our own socket
	char *port = strchr(conf->endpoint[conf->party], ':');
	check(port++, "node_new: invalid endpoint: %s", conf->endpoint[conf->party]);
	zsock_set_identity(self->socket, self->endpoint[conf->party]);
	status = zsock_bind(self->socket, "tcp://*:%s", port);
	check(status >= 0, "zsock_bind: %s", zmq_strerror(errno));
	// initiate connection to all peers that have a lower index
	for(int i = 0; i < conf->party; i++) {
		if(i == conf->party) continue;
		status = zsock_connect(self->socket, "tcp://%s", conf->endpoint[i]);
		check(status != -1, "zsock_connect: %s; %s", zmq_strerror(errno), conf->endpoint[i]);
	}
	// wait for probes from all parties
	for(int i = 0; i < conf->num_parties; i++) {
		if(i == conf->party) continue;
		zmsg_t *msg = zmsg_recv(self->socket);
		check(msg, "zmsg_recv: %s", zmq_strerror(errno));
		zmsg_destroy(&msg);
	}


	self->actor = zactor_new(node_actor, self);
	check(self->actor, "zactor_new: %s", zmq_strerror(errno));

	return 0;

error:
	if(nn) node_free(nn);
	return 1;
}

void node_free(node **nn) {
	if(nn && *nn) {
		node *self = *nn;
		if(self->actor) {
			zactor_destroy(&self->actor);
		}
		if(self->peer_map) {
			zhashx_destroy(&self->peer_map);
		}
		if(self->peer) {
			for(int i = 0; i < self->num_peers; i++) {
				if(self->peer[i]) zsock_destroy(self->peer + i);
			}
			free(self->peer);
		}
		if(self->peer_handler) {
			for(int i = 0; i < self->num_peers; i++) {
				// already gets destroyed by zhashx_destroy
				//if(self->peer_handler[i]) zsock_destroy(self->peer_handler + i);
			}
			free(self->peer_handler);
		}
		if(self->socket) {
			zsock_destroy(&self->socket);
		}
		free(*nn);
		*nn = NULL;
	}
}
