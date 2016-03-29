#include <obliv.h>
#include <stdio.h>
#include "linear.h"
#include "util.h"
#include "error.h"

const int precision = 16;

void read_ls_from_file(int party, char* filepath, linear_system_t* ls){
  FILE *file;
  file = fopen(filepath, "r");
  if(file == NULL) perror("Error opening file");

  // Read matrix A
  int n, m;
  int res = fscanf(file, "%d", &n);
  res = fscanf(file, "%d", &m);
  double** A = malloc(n*sizeof(double*)); 
  for(size_t i = 0; i < n; ++i) A[i] = malloc(m*sizeof(double));
  fixed32_t *A_fixed_prec = malloc(n*m*sizeof(fixed32_t));
  printf("A =\n");
  for(size_t i = 0; i < n; i++) {
    for(size_t j = 0; j < m; j++) {
      res = fscanf(file, "%lf", &A[i][j]);
      A_fixed_prec[i*n+j] = double_to_fixed(A[i][j], precision);
      printf("%f ", A[i][j]);
    }
    printf("\n");
  }
    
  // Read vector b
  int l;
  res = fscanf(file, "%d", &l);
  printf("b =\n");
  double* b = malloc(l*sizeof(double)); 
  fixed32_t *b_fixed_prec = malloc(l*sizeof(fixed32_t));
  for(size_t i = 0; i < l; i++) {
    res = fscanf(file, "%lf", &b[i]);
    b_fixed_prec[i] = double_to_fixed(b[i], precision);
    printf("%f ", b[i]);
  }
    
  // Read mask for A and compute masked A
  res = fscanf(file, "%d", &n);
  res = fscanf(file, "%d", &m);
  double** A_mask = malloc(n*sizeof(double*)); 
  for(size_t i = 0; i < n; ++i) A_mask[i] = malloc(m*sizeof(double));
  fixed32_t *A_mask_fixed_prec = malloc(n*m*sizeof(fixed32_t));
  fixed32_t *A_masked_fixed_prec = malloc(n*m*sizeof(fixed32_t));
  printf("\nA_mask =\n");
  for(size_t i = 0; i < n; i++) {
    for(size_t j = 0; j < m; j++) {
      res = fscanf(file, "%lf", &A_mask[i][j]);
      A_mask_fixed_prec[i*n+j] = double_to_fixed(A_mask[i][j], precision);
      A_masked_fixed_prec[i*n+j] = A_mask_fixed_prec[i*n+j] + A_fixed_prec[i*n+j];
      printf("%f ", A_mask[i][j]);
    }
    printf("\n");
  }
  
  // Read mask for b and compute masked b
  int res = fscanf(file, "%d", &l);
  printf("b_mask =\n");
  double* b_mask = malloc(l*sizeof(double)); 
  fixed32_t *b_masked_fixed_prec = malloc(l*sizeof(fixed32_t));
  fixed32_t *b_mask_fixed_prec = malloc(l*sizeof(fixed32_t));
  for(size_t i = 0; i < l; i++) {
    res = fscanf(file, "%lf", &b_mask[i]);
    b_mask_fixed_prec[i] = double_to_fixed(b_mask[i], precision);
    b_masked_fixed_prec[i] = b_mask_fixed_prec[i] + b_fixed_prec[i];
    printf("%f ", b_mask[i]);
  }
  printf("\n");

  fclose(file);

  // Construct instance ls
  ls->a.d[0] = m;
  ls->a.d[1] = ls->b.len = m;
  ls->precision = precision;
  if(party == 1) {
    ls->a.value = A_masked_fixed_prec;
    ls->b.value = b_masked_fixed_prec;
    ls->beta.value = NULL;
    ls->beta.len = -1;
  } else if(party == 2) {
    ls->a.value = A_mask_fixed_prec;
    ls->b.value = b_mask_fixed_prec;
    ls->beta.value = malloc(m*sizeof(fixed32_t));
    ls->beta.len = m;
  }
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

	ProtocolDesc pd;
	ocTestUtilTcpOrDie(&pd, party==1, argv[1]);
	setCurrentParty(&pd, party);
	void (*algorithms[])(void *) = {cholesky, ldlt};
	for(int i = 0; i < 2; i++) {
		double time = wallClock();
		execYaoProtocol(&pd, algorithms[i], &ls);

		if(party == 2) { 
		  //check(ls.beta.len == d, "Computation error.");
			printf("\n");
			printf("Algorithm: %s\n", i == 0 ? "Cholesky" : "LDL^T");
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
