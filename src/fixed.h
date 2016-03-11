#pragma once
#include <stdint.h>

typedef int32_t fixed32_t;

fixed32_t double_to_fixed(double d, int p);
double fixed_to_double(fixed32_t f, int p);
