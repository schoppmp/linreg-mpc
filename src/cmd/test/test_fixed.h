#pragma once
#include "fixed.h"

typedef struct protocolIO {
	fixed_t *inputs, result;
	size_t len, gates;
	int p;
} protocolIO;

void test_fixed(void *v);
