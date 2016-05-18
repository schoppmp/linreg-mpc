#pragma once
#include <stdio.h>

typedef struct _config {
	char **endpoint;
	ssize_t *index_owned;
	size_t n;
	size_t d;
	int party;
	int num_parties;
	FILE *input;
} config;

int config_new(config **c, const char *filename);

void config_free(config **c);
