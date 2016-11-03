#include "verification.h"
#include "check_error.h"
#include "linear.h"
#include "fixed.h"

#include <errno.h>
#include <obliv_common.h>
#include <bcrandom.h>
//#include <emp-m2pc/malicious.h>
#include <gcrypt.h>

static int run_verification_malicious(node *self, config *c) {
  gcry_mpi_t *v = NULL,
             temp = 0, 
             modul = 0;
  char *buf = NULL;
  bool *bits = NULL;
  size_t d = c->d;
  size_t bufsize = d * 2 * sizeof(ufixed_t);
  
  // initialize memory
  buf = malloc(bufsize);
  bits = malloc(FIXED_BIT_SIZE * 2 * d * sizeof(bool));
  v = calloc(d, sizeof(gcry_mpi_t));
  check(buf && v, "Out of memory");
  for(size_t i = 0; i < d; i++) {
    v[i] = gcry_mpi_new(FIXED_BIT_SIZE * 2);
  }
  // modul = 2 ^ (FIXED_BIT_SIZE * 2)
  modul = gcry_mpi_new(FIXED_BIT_SIZE * 2 + 1);
  gcry_mpi_set_bit(modul, FIXED_BIT_SIZE * 2);
  
  // receive vectors from data providers
  for(int p = 2; p < self->num_parties; p++) {
    check(orecv(self->peer[p], 0, buf, bufsize) == bufsize, 
      "orecv: %s", strerror(errno));
    for(size_t i = 0; i < d; i++) {
        gcry_error_t err;
        err = gcry_mpi_scan(&temp, GCRYMPI_FMT_USG, 
          buf + i * sizeof(ufixed_t) * 2, sizeof(ufixed_t) * 2, NULL);
        check(!gcry_err_code(err), "gcry_mpi_scan: %s", gcry_strerror(err));
        gcry_mpi_addm(v[i], v[i], temp, modul);
        gcry_mpi_release(temp);
    }
  }
  free(buf);
  gcry_mpi_release(temp);
  gcry_mpi_release(modul);
  
  // convert v to bit array
  for(size_t i = 0; i < d; i++) {
    for(unsigned int j = 0; j < FIXED_BIT_SIZE * 2; j++) {
      bits[FIXED_BIT_SIZE * i + j] = gcry_mpi_test_bit(v[i], j);
    }
    gcry_mpi_release(v[i]);
  }
  free(v);
  
  // start malicious GC with `bits' as inputs
  
  
  free(bits);
  
  return 0;
  
error:
  free(buf);
  free(bits);
  for(size_t i = 0; i < d; i++) {
    gcry_mpi_release(v[i]);
  }
  free(v);
  gcry_mpi_release(temp);
  gcry_mpi_release(modul);
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
  size_t bufsize = d * 2 * sizeof(ufixed_t);
  buf1 = malloc(bufsize);
  buf2 = malloc(bufsize);
  check(buf1 && buf2, "Out of memory");
  BCipherRandomGen *gen = newBCipherRandomGen();
  randomizeBuffer(gen, (char *) buf1, bufsize);
	releaseBCipherRandomGen(gen);
  for(size_t i = 0; i < d; i++) {
    gcry_error_t err;
    err = gcry_mpi_scan(&temp, GCRYMPI_FMT_USG, buf1 + i * sizeof(ufixed_t) * 2, 
      2 * sizeof(ufixed_t), NULL);
    check(!gcry_err_code(err), "gcry_mpi_scan: %s", gcry_strerror(err));
    gcry_mpi_subm(v[i], v[i], temp, modul);
    err = gcry_mpi_print(GCRYMPI_FMT_USG, buf2 + i * sizeof(ufixed_t) * 2, 
      2 * sizeof(ufixed_t), NULL, v[i]);
    check(!gcry_err_code(err), "gcry_mpi_print: %s", gcry_strerror(err));
    gcry_mpi_release(temp);
    gcry_mpi_release(v[i]);
  }
  gcry_mpi_release(modul);
  free(v);
  
  // send buf1 to CSP and buf2 to Evaluator
  check(osend(self->peer[0], 0, buf1, bufsize) == bufsize, 
    "osend: %s", strerror(errno));
  check(osend(self->peer[1], 0, buf2, bufsize) == bufsize, 
    "osend: %s", strerror(errno));
  
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
  if(self->party == 1 || self->party == 2) {
    return run_verification_malicious(self, c);
  } else if(self->party > 2 && self->party <= self->num_parties) {
    return run_verification_dp(self, c, share_A, share_b, beta, precision);
  }
  check(0, "Invalid party");

error:
  return 1;
}
