#pragma once
#include "obliv.h"
#include "config.h"

typedef struct node {
	int party;
	int num_parties;
	ProtocolDesc **peer;
} node;

int node_new(node **n, config *conf);

void node_destroy(node **n);
