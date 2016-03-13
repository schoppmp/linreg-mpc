# Secure distributed linear regression

A protocol for secure distributed linear regression.
Currently only consists of a few tests.

## Test fixed point arithmetic
This test computes the square root of the dot product of the two private input vectors.

Usage: `bin/test_fixed [Port] [Party] [Value]...`

In order to successfully build, [Obliv-C](https://github.com/samee/obliv-c/) must be installed. 
If the `oblivcc` executable is in the user's `PATH`, the `OBLIVCC` argument to `make` can be omitted.

```bash
mkdir bin
make OBLIVCC=/path/to/oblivcc
bin/test_fixed 1234 1 3 -1 0.5 2 1.33 &
bin/test_fixed 1234 2 5 11 0.5 10 -3
```
Output:
```
Time elapsed: 0.195243
Number of gates: 26308
Result: 4.501114
```
