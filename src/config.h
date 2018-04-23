#pragma once
#include <stdio.h>

typedef struct _config {
	int party;
	int num_parties;
	char **endpoint;
	ssize_t *index_owned;
	size_t n;
	size_t d;
	double normalizer1; // local normalization before phase 1
	size_t normalizer2; // normalization in the garbled circuit
	FILE *input;
} config;

int config_new(config **c, const char *filename);

void config_destroy(config **c);
