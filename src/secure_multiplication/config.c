#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>

#include "config.h"
#include "error.h"

int config_new(config **conf, const char *filename) {
	int status;
	config *c = NULL;
	check(conf && filename, "config_new: Arguments may not be null");
	
	// allocate config
	*conf = calloc(1, sizeof(config));
	check(*conf, "Out of memory");
	c = *conf;

	c->input = fopen(filename, "r");
	check(c->input, "fopen: %s", strerror(errno));

	// read configuration from input file and allocate memory
	status = fscanf(c->input, "%zd %zd %d", &c->n, &c->d, &c->num_parties);
	check(status == 3, "fscanf: %s", errno? strerror(errno) : "Invalid input");
	c->num_parties += 1; // include the TI
	c->endpoint = calloc(c->num_parties, sizeof(char *));
	check(c->endpoint, "out of memory");
	c->index_owned = calloc(c->num_parties, sizeof(ssize_t));
	check(c->index_owned, "out of memory");
	
	// read endpoints and array indices
	for(int i = 0; i < c->num_parties; i++) {
		status = fscanf(c->input, "%ms", c->endpoint + i);
		check(status == 1, "fscanf: %s", errno? strerror(errno) : "Invalid input");
		if(i == 0) {
			c->index_owned[0] = -1;
		} else {
			status = fscanf(c->input, "%zd", c->index_owned + i);
			check(status == 1, "fscanf: %s", errno? strerror(errno) : "Invalid input");
		}
	}
	
	return 0;

error:
	if(conf) {
		config_free(conf);
	}
	return 1;
}

void config_free(config **conf) {
	if(conf && *conf) {
		config *c = *conf;
		if(c->input) {
			fclose(c->input);
		}
		if(c->endpoint) {
			for(size_t i = 0; i < c->num_parties; i++) {
				free(c->endpoint[i]);
			}
			free(c->endpoint);
		}
		free(c->index_owned);
		free(c);
		*conf = NULL;
	}
}
