#pragma once
#include <stdint.h>

#if BIT_WIDTH_32

    #define FIXED_BIT_SIZE 32
    typedef int32_t fixed_t;
    typedef uint32_t ufixed_t;
    
#else

    #define FIXED_BIT_SIZE 64
    typedef int64_t fixed_t;
    typedef uint64_t ufixed_t;

#endif

fixed_t double_to_fixed(double d, int p);
double fixed_to_double(fixed_t f, int p);
