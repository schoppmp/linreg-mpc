#pragma once
#include <stdint.h>

#define FIXED_BIT_SIZE 32
typedef int32_t fixed32_t;

fixed32_t double_to_fixed(double d, int p);
double fixed_to_double(fixed32_t f, int p);
