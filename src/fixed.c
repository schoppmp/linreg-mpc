#include "fixed.h"

fixed64_t double_to_fixed(double d, int p) {
	return (fixed64_t) (d * (1 << p));
}

double fixed_to_double(fixed64_t f, int p) {
	return ((double) f) / (1 << p);
}

