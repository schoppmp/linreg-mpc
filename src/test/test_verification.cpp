#include "fixed.h"

#include <emp-tool/emp-tool.h>
#include <emp-m2pc/malicious.h>

// EMP forces us to use global variables, because circuit functions cannot
// take additional arguments for some reason
size_t d;
static const int MAX_DIFF = 10;

// Helper function that maps indices into a symmetric matrix
// to an index into a one-dimensional array.
// Copied from linear.c to save dependencies
static size_t idx(size_t i, size_t j) {
	if(j > i) {
		std::swap(i, j);
	}
	return (i * (i + 1)) / 2 + j;
}

// checks if the two vectors differ component-wise by `MAX_DIFF' at most
static void verify_difference(block * out, const block * in, const block * in2) {
  Bit result(true);
  for(size_t i = 0; i < d; i++) {
    Integer u(FIXED_BIT_SIZE, MAX_DIFF); // maximum allowed distance
    Integer a(FIXED_BIT_SIZE, in + i * FIXED_BIT_SIZE);
    Integer b(FIXED_BIT_SIZE, in2 + i * FIXED_BIT_SIZE);
    Integer c = a-b;
    result = result & !(c.abs().geq(u));
  }
  memcpy(out, &result, sizeof(block));
}

// verifies the solution to a linear system 
static void verify_solution(block *out, const block *in, const block *in2) {
  Integer *a = new Integer[d * (d+1) / 2];
  // assume the inputs first store b, then beta, then A
  for(size_t i = 0; i < d * (d+1) / 2; i++) {
    a[i] = Integer(FIXED_BIT_SIZE, in + (2 * d + i) * FIXED_BIT_SIZE) + 
      Integer(FIXED_BIT_SIZE, in2 + (2 * d + i) * FIXED_BIT_SIZE);
  }
  // compute a * beta and check if |a * beta - b| < u
  Bit result(true);
  Integer u(FIXED_BIT_SIZE, MAX_DIFF); // maximum allowed distance
  for(size_t i = 0; i < d; i++) {
    Integer b = Integer(FIXED_BIT_SIZE, in + i * FIXED_BIT_SIZE) + 
      Integer(FIXED_BIT_SIZE, in2 + i * FIXED_BIT_SIZE);
    Integer beta = Integer(FIXED_BIT_SIZE, in + (d + i) * FIXED_BIT_SIZE) + 
      Integer(FIXED_BIT_SIZE, in2 + (d + i) * FIXED_BIT_SIZE);
    Integer temp(FIXED_BIT_SIZE, 0ll);
    for(size_t j = 0; j < d; j++) {
      temp = temp + (a[idx(i,j)] * beta);
    }
    temp = temp - b;
    result = result & !(temp.abs().geq(u));
  }
  memcpy(out, &result, sizeof(block));
  
  delete[] a;
}



int main(int argc, char** argv) {
  int port, party;
  if(argc < 5) {
    cerr << "Usage: " << argv[0] << " Party Port d Version [Address]\n";
    exit(1);
  }
  parse_party_and_port(argv, &party, &port);
	if(party == BOB && argc < 6) {
		cerr << "Address argument is mandatory for party " << BOB << "\n";
		exit(1);
	}
  d = std::stoi(argv[3]);
  int version = std::stoi(argv[4]);
  size_t len;
    
  bool *in;
  void *f;
  if(version == 1) { // only check two vectors
    f = (void *) &verify_difference;
    len = d * FIXED_BIT_SIZE;
    in = new bool[len];
    for(size_t i = 0; i < d; i++) {
      int64_to_bool(in + i * FIXED_BIT_SIZE, i + 10 * party, FIXED_BIT_SIZE);
    }
  } else if(version == 2) { // check entire linear system
    f = (void *) &verify_solution;
    len = FIXED_BIT_SIZE * (2 * d + (d * (d+1) / 2));
    in = new bool[len];
    for(size_t i = 0; i < d; i++) {
      int64_to_bool(in + i * FIXED_BIT_SIZE, 2*d, FIXED_BIT_SIZE);
    }
    for(size_t i = 0; i < d; i++) {
      int64_to_bool(in + (d + i) * FIXED_BIT_SIZE, 1, FIXED_BIT_SIZE);
    }
    for(size_t i = 0; i < d * (d+1) / 2; i++) {
      int64_to_bool(in + (2 * d + i) * FIXED_BIT_SIZE, 1, FIXED_BIT_SIZE);
    }
  } else {
    cerr << "Version must be 1 or 2\n";
  }
  
  NetIO io(party==ALICE ? nullptr:"127.0.0.1", port);
  Malicious2PC<RTCktOpt::off> mal(&io, party, len, len, 1);
  double t1 = wallClock();
  if(party == ALICE) {
      mal.alice_run(f, in);
  } else {
      bool valid;
      mal.bob_run(f, in, &valid);
      cout << "result: " << (valid ? "valid" : "invalid") << "\n";
      double t2 = wallClock() - t1;
      cout << "time: "<< t2 << "\n";
  }
  delete[] in;
}
