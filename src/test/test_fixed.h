#pragma once
#include "fixed.h"

typedef struct protocolIO {
	fixed32_t *inputs, result;
	int len, p;
	int gates;
} protocolIO;

void test_fixed(void *v);
