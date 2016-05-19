#pragma once
#include <stdio.h>

typedef struct _config {
	char *endpoint_evaluator; // Evaluator is an additional party not counted in num_parties and with party=-1
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
