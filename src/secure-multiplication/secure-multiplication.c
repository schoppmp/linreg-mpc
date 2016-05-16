#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#include "secure-multiplication.h"
#include "node.h"
#include "config.h"
#include "error.h"
#include "../linear.h"


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

	printf("created node %d\n", party);

	/*if(c->party == 0) {
		status = run_trusted_initializer(c);
		check(status, "Error while running trusted initializer");
	} else {
		status = run_party(c);
		check(status, "Error while running party %d", c->party);
	}*/

	node_free(&self);
	config_free(&c);
	return 0;
error:
	config_free(&c);	
	node_free(&self);
	return 1;
}
