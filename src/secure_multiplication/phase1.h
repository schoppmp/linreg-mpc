#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

#include "secure_multiplication.pb-c.h"
#include "node.h"
#include "config.h"
#include "check_error.h"
#include "linear.h"
#include "fixed.h"

int run_trusted_initializer(
  node *self,
  config *c,
  int precision,
  bool use_ot
);
int run_party(
  node *self,
  config *c,
  int precision,
  struct timespec *wait_total,
  ufixed_t **res_A,
  ufixed_t **res_b,
  bool use_ot
);
