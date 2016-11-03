#include "fixed.h"

#include <emp-tool/emp-tool.h>
#include <emp-m2pc/malicious.h>

// EMP forces us to use global variables, because circuit functions cannot
// take additional arguments for some reason
size_t d, len;
int party;

static const int MAX_DIFF = 10;

// checks if the two vectors differ by `MAX_DIFF' at most
static void verification_circuit(block * out, const block * in, const block * in2) {
  Bit result = Bit(false);
  for(size_t i = 0; i < d; i++) {
    Integer u(FIXED_BIT_SIZE, MAX_DIFF); // maximum allowed distance
    Integer a(FIXED_BIT_SIZE, in + i * FIXED_BIT_SIZE);
    Integer b(FIXED_BIT_SIZE, in2 + i * FIXED_BIT_SIZE);
    Integer c = a-b;
    result = result | c.abs().geq(u);
    memcpy(out, &result, sizeof(block));
  }
}

int main(int argc, char** argv) {
  int port, party;
  if(argc < 4) {
    cerr << "Usage: " << argv[0] << " Party Port d\n";
    exit(1);
  }
  parse_party_and_port(argv, &party, &port);
  NetIO io(party==ALICE ? nullptr:"127.0.0.1", port);
  d = std::stoi(argv[3]);
  len = d * FIXED_BIT_SIZE;

  void * f = (void *)&verification_circuit;

  Malicious2PC<RTCktOpt::off> mal(&io, party, len, len, 1);
  double t1 = wallClock();
  
  bool *in = new bool[FIXED_BIT_SIZE * d];
  for(size_t i = 0; i < d; i++) {
    int64_to_bool(in + i * FIXED_BIT_SIZE, i + 10 * party, FIXED_BIT_SIZE);
  }
  if(party == ALICE) {
      mal.alice_run(f, in);
  } else {
      bool invalid;
      mal.bob_run(f, in, &invalid);
      cout << "result: " << (invalid ? "invalid" : "valid") << "\n";
      double t2 = wallClock() - t1;
      cout << "time: "<< t2 << "\n";
  }
  delete[] in;
}
