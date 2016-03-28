#include <obliv.h>
#include <stdio.h>
#include "linear.h"
#include "util.h"
#include "error.h"


const int precision = 16;
#define DIM 4

double a_d[DIM][DIM] = {{11,0.7,-3,-4},{0.7,8,2,-5},{-3,2,5,-6},{-4,-5,-6,123.456}};
double mask_a_d[DIM][DIM] = {{10, -0.20, -30, 0},{0.40, 50, -0.60, 0}, {7,8,9,0}, {12,34,56,789}};
double b_d[DIM] = {123,-456,7,-0.8};
double mask_b_d[DIM] = {555, -666, 0.777, -0.888};

int main(int argc, char **argv) {
	check(argc >= 3, "Usage: %s [Port] [Party]", argv[0]);

	linear_system_t ls;
	int d = DIM;

	// convert test data to fixed point
	fixed32_t *a = alloca(d*d*sizeof(fixed32_t));
	fixed32_t *mask_a = alloca(d*d*sizeof(fixed32_t));
	fixed32_t *b = alloca(d*sizeof(fixed32_t));
	fixed32_t *mask_b = alloca(d*sizeof(fixed32_t));

	for(size_t i = 0; i < d; i++) {
		for(size_t j = 0; j < d; j++) {
			mask_a[i*d+j] = double_to_fixed(mask_a_d[i][j], precision);
			a[i*d+j] = double_to_fixed(a_d[i][j], precision) + mask_a[i*d+j];
		}
		mask_b[i] = double_to_fixed(mask_b_d[i], precision);
		b[i] = double_to_fixed(b_d[i], precision) + mask_b[i];
	}

	ls.a.d[0] = ls.a.d[1] = ls.b.len = d;
	ls.precision = precision;

	// read party
	int party = 0;
	if(!strcmp(argv[2], "1")) {
		party = 1;
		ls.a.value = a;
		ls.b.value = b;
		ls.beta.value = NULL;
		ls.beta.len = -1;
	} else if(!strcmp(argv[2], "2")) {
		party = 2;
		ls.a.value = mask_a;
		ls.b.value = mask_b;
		ls.beta.value = alloca(d*sizeof(fixed32_t));
		ls.beta.len = d;
	}
	check(party > 0, "Party must be either 1 or 2.");
	ls.num_iterations = 10; // TODO: tune number

	ProtocolDesc pd;
	ocTestUtilTcpOrDie(&pd, party==1, argv[1]);
	setCurrentParty(&pd, party);
	void (*algorithms[])(void *) = {cholesky, ldlt, cgd};
	char *algorithm_names[] = {"Cholesky", "LDL^T", "Conjugate Gradient Descent"};
	for(int i = 0; i < 3; i++) {
		double time = wallClock();
		execYaoProtocol(&pd, algorithms[i], &ls);

		if(party == 2) { 
			check(ls.beta.len == d, "Computation error.");
			printf("\n");
			printf("Algorithm: %s\n", algorithm_names[i]);
			printf("Time elapsed: %f\n", wallClock() - time);
			printf("Number of gates: %d\n", ls.gates);
			printf("Result: ");
			for(size_t i = 0; i < ls.beta.len; i++) {
				printf("%f ", fixed_to_double(ls.beta.value[i], precision));
			}
			printf("\n");
		}
	}
	cleanupProtocol(&pd);

	return 0;
error:
	return 1;
}
