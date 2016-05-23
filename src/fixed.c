#include "fixed.h"

fixed64_t double_to_fixed(double d, int p) {
	return (fixed64_t) (d * (1ll << p));
}

double fixed_to_double(fixed64_t f, int p) {
	return ((double) f) / (1ll << p);
}

