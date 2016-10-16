#include "fixed.h"

fixed_t double_to_fixed(double d, int p) {
	return (fixed_t) (d * (1ll << p));
}

double fixed_to_double(fixed_t f, int p) {
	return ((double) f) / (1ll << p);
}

