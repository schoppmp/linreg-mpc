#include <errno.h>
#include <stdio.h>
#include "fixed.h"
#include "linear.h"
#include "error.h"

size_t idx(size_t i, size_t j) {
	if(j > i) {
		i^=j; j^=i; i^=j;
	}
	return (i * (i + 1)) / 2 + j;
}


int read_matrix(FILE *file, matrix_t *matrix, int precision) {
	int n, m, res;
	check(matrix && file, "Arguments may not be null.");
	matrix->value = NULL;

	res = fscanf(file, "%d", &n);
	check(res == 1, "fscanf: %s.", strerror(errno));
	res = fscanf(file, "%d", &m);
	check(res == 1, "fscanf: %s.", strerror(errno));


	matrix->d[0] = n;
	matrix->d[1] = m;
	matrix->value = malloc(n*m*sizeof(fixed64_t));

//	printf("A = \n");
	for(size_t i = 0; i < n; i++) {
		for(size_t j = 0; j < m; j++) {
			double val;
			res = fscanf(file, "%lf", &val);
			check(res == 1, "fscanf: %s.", strerror(errno));
			matrix->value[i*m+j] = double_to_fixed(val, precision);
//			printf("%f ", val);
		}
//		printf("\n");
	}

	return 0;
	
error:
	if(matrix) {
		matrix->d[0] = matrix->d[1] = 0;
		free(matrix->value);
		matrix->value = NULL;
	}
	return 1;	
}

int read_vector(FILE *file, vector_t *vector, int precision) {
	int l, res;
	check(vector && file, "Arguments may not be null.");

	res = fscanf(file, "%d", &l);
	check(res == 1, "fscanf: %s.", strerror(errno));

	vector->len = l;
	vector->value = malloc(l * sizeof(fixed64_t));

//	printf("l = %d, b = \n", l);
	for(size_t i = 0; i < l; i++) {
		double val;
		res = fscanf(file, "%lf", &val);
		check(res == 1, "fscanf: %s.", strerror(errno));
		vector->value[i] = double_to_fixed(val, precision);
//		printf("%f ", val);
	}
//	printf("\n");

	return 0;

error:
	if(vector) {
		vector->len = 0;
		free(vector->value);
		vector->value = NULL;
	}
	return 1;

}
