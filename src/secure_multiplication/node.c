#include <string.h>
#include <errno.h>
#include <unistd.h>

#include "node.h"
#include "obliv.h"
#include "obliv_common.h"
#include "check_error.h"
#include "util.h"

int node_new(node **nn, config *conf) {
	int status;
	char *host = NULL;
	check(nn && conf, "node_new: Arguments may not be null");

	*nn = malloc(sizeof(node));
	check(*nn, "out of memory");
	node *n = *nn;
	n->num_parties = conf->num_parties;
	n->party = conf->party;
	n->peer = calloc(n->num_parties, sizeof(ProtocolDesc *));
	check(n->peer, "out of memory");

	int i;
	// other peer is listening -> connect
	for(i = 0; i < n->party - 1; i++) {
		host = strdup(conf->endpoint[i]);
		check(host, "out of memory");
		char* port = strchr(host, ':');
		*(port++) = '\0'; // split endpoint at ':'
		n->peer[i] = calloc(1, sizeof(ProtocolDesc));
		check(n->peer[i], "out of memory");
		util_loop_connect(n->peer[i], host, port);
		free(host);
		check(osend(n->peer[i], 0, &(n->party), sizeof(n->party)) == sizeof(n->party),
			"Party %d: osend: %s", n->party, strerror(errno)); // announce ourselves
		orecv(n->peer[i],0,NULL,0); // flush
	}

	// open our own listening socket
	int listen_sock;
	check(i == n->party - 1, "WAT");
	n->peer[i] = NULL;
	char* port = strchr(conf->endpoint[i], ':') +1;
	listen_sock = tcpListenAny(port);
	check(listen_sock >= 0, "Could not create listen socket");

	// accept incoming connections from peers
	for(i = n->party; i < n->num_parties; i++) {
		ProtocolDesc *pd = calloc(1, sizeof(ProtocolDesc));
		check(pd, "out of memory");
		int sock = accept(listen_sock, NULL, NULL);
		protocolUseTcp2P(pd,sock,false);
		int other;
		check(orecv(pd, 0, &other, sizeof(other)) == sizeof(other),
			"Party %d: orecv: %s", n->party, strerror(errno));
		check(other > n->party && other <= n->num_parties,
			"Party %d received invalid party number %d from remote", n->party, other);
		check(n->peer[other-1] == NULL,
			"Duplicate party %d", other);
		n->peer[other-1] = pd;
	}
	close(listen_sock);
	return 0;

error:
	free(host);
	if(nn) node_destroy(nn);
	return 1;
}

void node_destroy(node **nn) {
	if(nn && *nn) {
		node *n = *nn;
		for(int i = 0; i < n->num_parties; i++) {
			if(n->peer[i]) {
				cleanupProtocol(n->peer[i]);
				free(n->peer[i]);
			}
		}
		free(n->peer);
		free(n);
		*nn = NULL;
	}
}
