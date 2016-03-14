# Secure distributed linear regression

A protocol for secure distributed linear regression.
Currently only consists of a few tests.
In order to successfully build, [Obliv-C](https://github.com/samee/obliv-c/) must be installed. 
If the `oblivcc` executable is not in the user's `PATH`, the `OBLIVCC` variable must be set when calling `make`
```
make OBLIVCC=/path/to/oblivcc
```

## Test Cholesky decomposition
Solves a simple 4x4 linear system using cholesky decomposition.

Usage: `bin/test_linear_system [Port] [Party]`

```
make bin/test_linear_system 
bin/test_linear_system 1234 1 &
bin/test_linear_system 1234 2
```
Output:
```
Algorithm: Cholesky
Time elapsed: 0.435625
Number of gates: 176461
Result: 28.825195 -71.199692 47.603928 0.357391 

Algorithm: LDL^T
Time elapsed: 0.348329
Number of gates: 174943
Result: 28.824432 -71.199356 47.602890 0.357407 
```
Note that LDL^T uses slightly fewer garbled gates.
To compare the accuracy, see the [solution](http://www.wolframalpha.com/input/?i=LinearSolve[{{11,0.7,-3,-4},{0.7,8,2,-5},{-3,2,5,-6},{-4,-5,-6,123.456}},{123,-456,7,-0.8}]]) with data shared in plaintext.

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
