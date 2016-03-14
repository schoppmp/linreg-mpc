# Secure distributed linear regression

A protocol for secure distributed linear regression.
Currently only consists of a few tests.
In order to successfully build, [Obliv-C](https://github.com/samee/obliv-c/) must be installed. 
If the `oblivcc` executable is not in the user's `PATH`, the `OBLIVCC` variable must be set when calling `make`
```
make OBLIVCC=/path/to/oblivcc
```

## Test Cholesky decomposition
Solves a simple 3x3 linear system using cholesky decomposition.

Usage: `bin/test_cholesky [Port] [Party]`

```
make bin/test_cholesky
bin/test_cholesky 1234 1 & 
bin/test_cholesky 1234 2
```
Output:
```
Time elapsed: 0.370451
Number of gates: 99180
Result: -0.319016 0.368103 0.644165 
```

## Test fixed point arithmetic
This test computes the square root of the dot product of the two private input vectors.

Usage: `bin/test_fixed [Port] [Party] [Value]...`

```bash
make bin/test_fixed
bin/test_fixed 1234 1 3 -1 0.5 2 1.33 &
bin/test_fixed 1234 2 5 11 0.5 10 -3
```
Output:
```
Time elapsed: 0.195243
Number of gates: 26308
Result: 4.501114
```
