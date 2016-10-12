
#include <stdint.h>

#if BIT_WIDTH_32

    #define FIXED_BIT_SIZE 32
    typedef int32_t fixed64_t;
    
#else

    #define FIXED_BIT_SIZE 64
    typedef int64_t fixed64_t;

#endif

fixed64_t double_to_fixed(double d, int p);
double fixed_to_double(fixed64_t f, int p);
