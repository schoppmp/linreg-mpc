#pragma once

#include "secure_multiplication/node.h"
#include "fixed.h"

#ifdef __cplusplus
#define EXTERNC extern "C"
#else
#define EXTERNC
#endif

EXTERNC int run_verification(
  node *self,
  config *c,
  ufixed_t *share_A,
  ufixed_t *share_b,
  ufixed_t *beta,
  int precision
);

#undef EXTERNC
