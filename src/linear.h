#pragma once
#include "fixed.h"

typedef struct {
	size_t d[2];
	fixed32_t *value;
} matrix_t;

typedef struct {
	size_t len;
	fixed32_t *value;
} vector_t;

typedef struct {
	matrix_t a;
	vector_t b;
	vector_t beta;
	int precision;
	int gates;
} linear_system_t;

// helper function that maps indices into a symmetric matrix
// to an index into a one-dimensional array
size_t idx(size_t i, size_t j);

// functions to solve LSs
void cholesky(void *);
void ldlt(void *);

// IO helpers
int read_matrix(FILE *, matrix_t *, int);
int read_vector(FILE *, vector_t *, int);
