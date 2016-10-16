#pragma once
#include<obliv_types_internal.h>
#include "secure_multiplication/node.h"
#include "fixed.h"

typedef struct DualconR DualconR;
typedef struct DualconS DualconS;

DualconS* dcsConnect(node *self);
void dcsSendIntArray(DualconS* con,const ufixed_t* input,size_t n);
void dcsClose(DualconS* con);

DualconR* dcrConnect(node *self);
void dcrRecvBitArray(DualconR* con,OblivBit* dest,size_t n,int party);
#ifdef __oblivious_c
static inline void
dcrRecvIntArray(DualconR* con,obliv ufixed_t* input,size_t n,int party)
  { dcrRecvBitArray(con,(OblivBit*)input,n*ocBitSize(*input),party); }
#endif
void dcrClose(DualconR* con);
