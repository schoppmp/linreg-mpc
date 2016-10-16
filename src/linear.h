#pragma once
#include <stdio.h>
#include "fixed.h"
#include "secure_multiplication/node.h"

typedef struct {
	size_t d[2];
	fixed_t *value;
} matrix_t;

typedef struct {
	size_t len;
	fixed_t *value;
} vector_t;

typedef struct {
	matrix_t a;
	vector_t b;
	vector_t beta;
	int precision;
	long long gates;
	int num_iterations; // for cgd
	node *self; // for reading input from data providers
} linear_system_t;

// helper function that maps indices into a symmetric matrix
// to an index into a one-dimensional array
size_t idx(size_t i, size_t j);

// inner product of two vectors of the same length
fixed_t inner_product(vector_t *, vector_t *);

// functions to solve LSs
void cholesky(void *);
void ldlt(void *);
void cgd(void *);

// IO helpers
int read_matrix(FILE *, matrix_t *, int);
int read_vector(FILE *, vector_t *, int);
