# Secure distributed linear regression

A protocol for secure distributed linear regression.
In order to successfully build, [Obliv-C](https://github.com/samee/obliv-c/) must be installed and the `OBLIVC_PATH` environment variable must point to its directory.

Then, in order to compile, run
```
git submodule update --init && make
```
By default, computations are performed using 64 bit fixed-point arithmetic. 
To enable 32 bit computations at compile time, the additional flag `BIT_WIDTH_32=1` must be passed to `make`.
This will increase computation speed, but may also reduce the accuracy of the results in some cases.


## Running experiments
The protocol consists of two phases. `bin/main` is used to run both phases at once.
```
Usage: bin/main [Input_file] [Precision] [Party] [Algorithm] [Num. iterations CGD]
```
`[Precision]` specifies the number of bits used for the fractional part of fixed-point encoded numbers.
The role of the process is given by `[Party]`. 
Values of 1 and 2 denote the CSP and Evaluator, respectively. 
Higher values denote data providers.
`[Algorithm]` is the algorithm used for phase 2 of the protocol and can be either `cholesky`, `ldlt`, or `cgd`.
In the case of CGD, `[Num. iterations CGD]` gives the number of iterations used before terminating.
An example input file is 
```
10 5 3
localhost:1234
localhost:1235
localhost:1236 0
localhost:1237 1
localhost:1238 2
10 5
-0.49490189906 0.204027068031 1.0 -0.0048744428595 0.101856000869 
0.49217428514 0.233090721372 -0.0370213771185 0.657720359628 0.525310770733 
0.39721227919 -0.470002959473 0.277398798616 0.726013362994 0.498046786861 
-0.595183792269 -0.0827269428691 -0.227611333929 0.80744916955 0.543968791627 
-0.419150270985 0.292994257369 -0.0232190555386 -0.108185527543 0.238913650953 
-0.247990663017 -1.0 -0.0241769053355 -0.842345696475 -1.0 
-1.0 0.437037219652 -0.140750839011 1.0 -0.0679355153937 
0.777015345458 0.981488358907 0.2870338525 0.579832272908 -0.262265338898 
-0.0431656936622 0.0910166551363 -0.0724090181375 -0.144008713528 0.202706144381 
-0.470188350902 -0.261201944989 -0.0468243599479 0.944605903172 0.455480894023 
10
0.463624257142 1.03914869701 0.641866385451 -0.289962112725 -0.328203220996 -1.64668349374 -0.205128259075 2.13151959591 -0.129983842519 -0.0766970254399 
```
It contains the number of samples, features and parties, followed by a network endpoint for each party. 
The special roles CSP and Evaluator are defined by the first two lines. 
Then, the data providers follow (3 in this example), each with a network endpoint and the starting index of its partition.
Afterwards, the dimensions of `X` are specified, followed by `X` itself. 
Finally, the length and values of `y` are given.

Running this example locally with
```
for party in {1..5}; do bin/main input_file 56 $party cholesky 1 & done
```
yields the following result
```
OT time: 0.301697
Time elapsed: 4.404333
Number of gates: 3173835
Result:    1.000359530238633    0.797558559108423    0.781463858861025    0.605140672557234    0.046213483377146 
```
