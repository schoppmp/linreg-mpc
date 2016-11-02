#include "verification.h"
#include "check_error.h"
#include "linear.h"
#include "fixed.h"

#include <obliv_common.h>
//#include <emp-m2pc/malicious.h>
#include <gcrypt.h>

static int run_verification_csp(node *self, config *c) {
  return 1;
}

static int run_verification_evaluator(node *self, config *c) {
  return 1;
}

static int run_verification_dp(
  node *self, 
  config *c,
  ufixed_t *share_A, 
  ufixed_t *share_b, 
  ufixed_t *beta,
  int precision
) {
  gcry_mpi_t *v = NULL, 
             temp = 0, 
             modul = 0;
               
  char *buf1 = NULL, *buf2 = NULL;
  size_t d = c->d;
  
  check(share_A, "`share_A' may not be NULL");
  check(share_b, "`share_b' may not be NULL");
  check(beta, "`beta' may not be NULL");
  
  // compute share_A * beta - share_b
  v = calloc(d, sizeof(gcry_mpi_t));
  temp = gcry_mpi_new(FIXED_BIT_SIZE * 2);
  // modul = 2 ^ (FIXED_BIT_SIZE * 2)
  modul = gcry_mpi_new(FIXED_BIT_SIZE * 2 + 1);
  gcry_mpi_set_bit(modul, FIXED_BIT_SIZE * 2);
  for(size_t i = 0; i < d; i++) {
    v[i] = gcry_mpi_new(FIXED_BIT_SIZE * 2);
    for(size_t j = 0; j < d; j++) {
      gcry_mpi_set_ui(temp, share_A[idx(i,j)]);
      gcry_mpi_mul_ui(temp, temp, beta[j]);
      gcry_mpi_add(v[i], v[i], temp);
    }
    gcry_mpi_set_ui(temp, share_b[i]);
    gcry_mpi_lshift(temp, temp, precision);
    gcry_mpi_subm(v[i], v[i], temp, modul);
  }
  gcry_mpi_release(temp);
  
  // split v into two additive shares
  buf1 = gcry_random_bytes(d * FIXED_BIT_SIZE * 2, GCRY_STRONG_RANDOM);
  buf2 = malloc(c->d * FIXED_BIT_SIZE * 2);
  for(size_t i = 0; i < d; i++) {
    gcry_mpi_scan(&temp, GCRYMPI_FMT_USG, buf1 + i * d, FIXED_BIT_SIZE * 2, NULL);
    gcry_mpi_subm(v[i], v[i], temp, modul);
    gcry_mpi_print(GCRYMPI_FMT_USG, buf1 + i * d, FIXED_BIT_SIZE * 2, NULL, v[i]);
    gcry_mpi_release(temp);
    gcry_mpi_release(v[i]);
  }
  gcry_mpi_release(modul);
  free(v);
  
  // send buf1 to CSP and buf2 to Evaluator
  osend(self->peer[0], 0, buf1, d * FIXED_BIT_SIZE * 2);
  osend(self->peer[1], 0, buf2, d * FIXED_BIT_SIZE * 2);
  
  free(buf1);
  free(buf2);
  return 0;
  
error:
  free(buf1);
  free(buf2);
  gcry_mpi_release(temp);
  gcry_mpi_release(modul);
  for(size_t i = 0; i < d; i++) {
    gcry_mpi_release(v[i]);
  }
  free(v);
  return 1;
}

int run_verification(
  node *self, 
  config *c,
  ufixed_t *share_A, 
  ufixed_t *share_b, 
  ufixed_t *beta,
  int precision
) {
  check(self, "`self' may not be NULL");
  check(c, "`c' may not be NULL");
  if(self->party == 1) {
    return run_verification_csp(self, c);
  } else if(self->party == 2) {
    return run_verification_evaluator(self, c);
  } else if(self->party > 2 && self->party <= self->num_parties) {
    return run_verification_dp(self, c, share_A, share_b, beta, precision);
  }
  check(0, "Invalid party");

error:
  return 1;
}
