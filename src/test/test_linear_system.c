#include <errno.h>
#include <obliv.h>
#include <stdio.h>
#include "linear.h"
#include "util.h"
#include "error.h"

const int precision = 16;

int read_ls_from_file(int party, const char *filepath, linear_system_t *ls) {
	FILE *file = NULL;
	int res;
	matrix_t A, A_mask;
	vector_t b, b_mask;
	A.value = A_mask.value = b.value = b_mask.value = NULL;

	check(ls && filepath, "Arguments may not be null.");
	file = fopen(filepath, "r");
	//check(file, "Could not open file: %s.", strerror(errno));

	// Read linear system from file
	res = read_matrix(file, &A, precision);
	check(!res, "Could not read A.");
	res = read_vector(file, &b, precision);
	check(!res, "Could not read b.");
	res = read_matrix(file, &A_mask, precision);
	check(!res, "Could not read A_mask.");
	res = read_vector(file, &b_mask, precision);
	check(!res, "Could not read b_mask.");
	for(size_t i = 0; i < A.d[0]; i++) {
		for(size_t j = 0; j < A.d[1]; j++) {
			A.value[i*A.d[1]+j] += A_mask.value[i*A.d[1]+j];
		}
		b.value[i] += b_mask.value[i];
	}

	fclose(file);
	file = NULL;

	// Construct instance ls
	ls->precision = precision;
	if(party == 1) {
		ls->a = A;
		ls->b = b;
		ls->beta.value = NULL;
		ls->beta.len = -1;
		free(A_mask.value);
		free(b_mask.value);
	} else {
		ls->a = A_mask;
		ls->b = b_mask;
		ls->beta.value = malloc(A_mask.d[1]*sizeof(fixed32_t));
		ls->beta.len = A_mask.d[1];
		free(A.value);
		free(b.value);
	}
	return 0;

	printf("mark0\n");

error:	// for some reason, oblivc removes this label if the stuff 
	// below isn't commented out. TODO: fix this and do proper cleanup
	/* fclose(file);
	free(A_mask.value);
	free(b_mask.value);
	free(A.value);
	free(b.value);*/
	return 1;
}


int main(int argc, char **argv) {
	check(argc >= 3, "Usage: %s [Port] [Party] [Input file]", argv[0]);
	int party = 0;
	if(!strcmp(argv[2], "1")) {
		party = 1;
	} else if(!strcmp(argv[2], "2")) {
		party = 2;
	}
	check(party > 0, "Party must be either 1 or 2.");

	linear_system_t ls;
	read_ls_from_file(party, argv[3], &ls);
	ls.num_iterations = ls.b.len; // TODO: tune number

	ProtocolDesc pd;
	ocTestUtilTcpOrDie(&pd, party==1, argv[1]);
	setCurrentParty(&pd, party);
	void (*algorithms[])(void *) = {cholesky, ldlt, cgd};
	char *algorithm_names[] = {"Cholesky", "LDL^T", "Conjugate Gradient Descent"};
	for(int i = 0; i < 3; i++) {
		double time = wallClock();
		execYaoProtocol(&pd, algorithms[i], &ls);

		if(party == 2) { 
		  //check(ls.beta.len == d, "Computation error.");
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
