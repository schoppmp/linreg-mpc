#pragma once
#include <stdio.h>

typedef struct _config {
	int party;
	int num_parties;
	char **endpoint;
	ssize_t *index_owned;
	size_t n;
	size_t d;
	FILE *input;
} config;

int config_new(config **c, const char *filename);

void config_destroy(config **c);
