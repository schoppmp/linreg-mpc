#pragma once
#include <stdint.h>

#define FIXED_BIT_SIZE 64
typedef int32_t fixed32_t;
typedef int64_t fixed64_t;

fixed64_t double_to_fixed(double d, int p);
double fixed_to_double(fixed64_t f, int p);
