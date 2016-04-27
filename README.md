# Secure distributed linear regression

A protocol for secure distributed linear regression.
In order to successfully build, [Obliv-C](https://github.com/samee/obliv-c/) must be installed. 
If the `oblivcc` executable is not in the user's `PATH`, the `OBLIVCC` variable must be set when calling `make`
```
make OBLIVCC=/path/to/oblivcc
```

## Running experiments
Currently, the main executable is `bin/test_linear_system`. It's used as follows.
```
Usage: bin/test_linear_system [Port] [Party] [Input file] [Algorithm] [Num. iterations CGD]
```
Here, `[Port]` is any free TCP port, `[Party]` is either 1 or 2, `[Algorithm]` is one of `cholesky`, `ldlt`, or `cgd`, `[Num. iterations CGD]` is the number of iterations to use if the algorithm is `cgd`. An example of an input file is
```
8 8
0.851447125526 0.0965869276121 -0.167866519707 0.0758683165702 0.052126333866 -0.124315546366 0.0241132623512 -0.04902811601 
0.0965869276121 1.01824877393 -0.128795347953 -0.123182450954 -0.0336023472075 -0.051463268361 0.131561510783 0.0284940396008 
-0.167866519707 -0.128795347953 0.898418769748 0.0211685414555 0.0957060857581 0.181385908161 -0.153407930335 -0.0762503314954 
0.0758683165702 -0.123182450954 0.0211685414555 0.932434046444 0.0799335461038 0.0923715997233 0.106194018749 -0.237349524061 
0.052126333866 -0.0336023472075 0.0957060857581 0.0799335461038 1.12278460092 0.164622799084 0.0286953587736 -0.0344822795687 
-0.124315546366 -0.051463268361 0.181385908161 0.0923715997233 0.164622799084 0.787842405466 0.0990583977867 -0.105985137045 
0.0241132623512 0.131561510783 -0.153407930335 0.106194018749 0.0286953587736 0.0990583977867 0.987266908629 -0.10984744972 
-0.04902811601 0.0284940396008 -0.0762503314954 -0.237349524061 -0.0344822795687 -0.105985137045 -0.10984744972 0.825145254223 
8
0.596257485514 0.310960858679 -1.04861414407 -0.727716967353 -1.12901485483 -1.05921194927 -0.471366796671 0.913373902227 
8
0.571828325968 0.065958003586 -0.820782164141 -0.422046020722 -0.794872994949 -0.691505010614 -0.404688627994 0.76546586242 
```
It consists of 
- The dimensions of matrix `A`
- The matrix `A` itself
- The length of vector `b`
- The vector `b`
- The length of `x`
- The solution `x` of the linear system `Ax=b`

The results of the computation are printed to the standard output:
```
bin/test_linear_system 1234 2 example.txt cholesky

Algorithm: cholesky
Time elapsed: 1.061934
Number of gates: 812339
Result:    0.571828544139862    0.065958380699158   -0.820781826972961   -0.422045469284058   -0.794872820377350   -0.691504597663879   -0.404688179492950    0.765466809272766 
```

Random input files can be generated using the script `generate_tests.py`:
```
usage: generate_tests.py [-h] [--verbose] n d dest_folder num_matrices
```
It generates `num_matrices` matrices `X` of dimensions `n, d`, as well as vectory `y` of length `n`, and writes matrices `A = X.T X` and vectors `b = A y` and `y` to files in `dest_folder`.

Finally, the script `test_lin_reg.py` can be used to run an entire batch of experiments.
```
usage: test_lin_reg.py [-h] [--verbose]
                       exec_path algorithm n d num_iters_cgd dest_folder
                       num_examples port
```
`exec_path` is the path to the `test_linear_system` executable, `algorithm` is one of `cholesky`, `ldlt`, `cgd`, or `all`, `n` and `d` are the dimensions of the generated examples, `num_iters_cgd` is the number of iterations for algorithm `cgd`, `dest_folder` is the folder where examples and output data are stored, `num_examples` is the number of examples to run for each algorithm and `port` is the TCP port to use. 

For each algorithm, two files are generated. One `.exec`-file, which contains the standard output of the call to `test_linear_system`, and one `.out`-file which contains aggregated statistics that can then be plotted.
