#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sodium.h>
#include <time.h>

#include "secure_multiplication.pb-c.h"
#include "secure_multiplication.h"
#include "node.h"
#include "config.h"
#include "check_error.h"
#include "linear.h"

int run_trusted_initializer(node *self, config *c);
int run_party(node *self, config *c, int precision, struct timespec *wait_total, uint32_t **res_A, uint32_t **res_b);