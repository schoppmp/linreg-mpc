#include <obliv.h>
#include <stdio.h>
#include "test/test_fixed.h"
#include "util.h"

// convenient error handling
#define check(cond, format, ...) \
	do {if(!(cond)) { \
		fprintf(stderr, format "\n", ##__VA_ARGS__); \
		goto error; \
	}} while(0);


const int precision = 8;

int main(int argc, char **argv) {
	ProtocolDesc pd;
	protocolIO io;

	check(argc >= 4, "Usage: %s [Port] [Party] [Value]...", argv[0]);

	// read party
	int party = 0;
	if(!strcmp(argv[2], "1")) {
		party = 1;
	} else if(!strcmp(argv[2], "2")) {
		party = 2;
	}
	check(party > 0, "Party must be either 1 or 2.");

	// read inputs
	io.p = precision;
	io.len = argc - 3;
	io.inputs = alloca(io.len * sizeof(fixed32_t));
	for(int i = 0; i < io.len; i++) {
		double d;
		check(sscanf(argv[i+3], "%lf", &d) == 1, "Error scanning argument number %d.", i+3);
		io.inputs[i] = double_to_fixed(d, precision);
	}
	
	double time = wallClock();
	ocTestUtilTcpOrDie(&pd, party==1, argv[1]);
	setCurrentParty(&pd, party);
	execYaoProtocol(&pd, test_fixed, &io);
	cleanupProtocol(&pd);

	if(party == 1) { 
		check(io.len != -1, "Input sizes do not match.");
		printf("Time elapsed: %f\n", wallClock() - time);
		printf("Number of gates: %d\n", io.gates);
		printf("Result: %f\n", fixed_to_double(io.result, precision));
	}

	return 0;
error:
	return 1;
}
