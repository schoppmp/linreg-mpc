#include <obliv.h>
#include <stdio.h>
#include "test/test_fixed.h"
#include "util.h"
#include "check_error.h"


const int precision = 56;
const int len = 1000000;

int main(int argc, char **argv) {
	ProtocolDesc pd;
	protocolIO io = {0};
	int ret = 1;

	//check(argc >= 4, "Usage: %s [Port] [Party] [Value]...", argv[0]);
	check(argc >= 3, "Usage: %s Port Party");

	// read party
	int party = 0;
	if(!strcmp(argv[2], "1")) {
		party = 1;
	} else if(!strcmp(argv[2], "2")) {
		party = 2;
	}
	check(party > 0, "Party must be either 1 or 2.");

	// generate inputs
	io.p = precision;
	//io.len = argc - 3;
	io.len = len;
	io.inputs = malloc(io.len * sizeof(fixed_t));
	for(int i = 0; i < io.len; i++) {
		double d = (double)rand() / RAND_MAX;
		// double d;
		// check(sscanf(argv[i+3], "%lf", &d) == 1, "Error scanning argument number %d.", i+3);
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
	free(io.inputs);
	ret = 0;
	
error:
	return ret;
}
