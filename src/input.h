#pragma once
#include<obliv_types_internal.h>

typedef struct DualconR DualconR;
typedef struct DualconS DualconS;

DualconS* dcsConnect(const char* csp_server,const char* csp_port,
                     const char* eval_server,const char* eval_port,
                     int party);
void dcsSendIntArray(DualconS* con,const uint64_t* input,int n);
void dcsClose(DualconS* con);

DualconR* dcrConnect(const char* port,int partyCount);
void dcrRecvBitArray(DualconR* con,OblivBit* dest,int n,int party);
#ifdef __oblivious_c
static inline void 
dcrRecvIntArray(DualconR* con,obliv uint64_t* input,int n,int party)
  { dcrRecvBitArray(con,(OblivBit*)input,n*ocBitSize(*input),party); }
#endif
void dcrClose(DualconR* con);
