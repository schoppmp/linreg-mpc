#pragma once
#include <stdio.h>

// convenient error handling
#define check(cond, format, ...) \
	do {if(!(cond)) { \
		fprintf(stderr, format "\n", ##__VA_ARGS__); \
		goto error; \
	}} while(0);

