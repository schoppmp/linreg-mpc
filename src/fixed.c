#include "fixed.h"

fixed32_t double_to_fixed(double d, int p) {
	return (fixed32_t) (d * (1 << p));
}

double fixed_to_double(fixed32_t f, int p) {
	return ((double) f) / (1 << p);
}

