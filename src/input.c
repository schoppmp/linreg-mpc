#include"input.h"
#include "util.h"
#include<obliv_types_internal.h>
#include<obliv_common.h>
#include<obliv_yao.h>
#include<obliv.h>
#include<assert.h>
#include<error.h>
#include<errno.h>
#include <unistd.h>
#include "secure_multiplication/node.h"
#include "fixed.h"

struct DualconS
{ node *self;
  struct HonestOTExtRecver* r;
};
static void flush(ProtocolDesc* pd)
{
  orecv(pd,0,NULL,0); // hack that causes two parties to flush
}
DualconS* dcsConnect(node *self)
{
  DualconS* dcs = malloc(sizeof(*dcs));
  dhRandomInit();
  dcs->self = self;
  dcs->r = honestOTExtRecverNew(self->peer[0],0);
  return dcs;
}
void dcsClose(DualconS* dcs)
{
  honestOTExtRecverRelease(dcs->r);
  free(dcs);
}
static const int intsize = FIXED_BIT_SIZE;
void dcsSendIntArray(DualconS* dcs,const ufixed_t* input,size_t n)
{
  size_t i,j,nn = n*intsize;
  bool* sel = malloc(nn*sizeof(bool));
  char* buf = malloc(nn*YAO_KEY_BYTES);
  for(i=0;i<n;++i) for(j=0;j<intsize;++j) sel[i*intsize+j]=((input[i]>>j)&1);
  // receive keys from CSP
  honestOTExtRecv1Of2(dcs->r,buf,sel,nn,YAO_KEY_BYTES);
  // send keys to Evaluator
  osend(dcs->self->peer[1],0,buf,nn*YAO_KEY_BYTES);
  flush(dcs->self->peer[1]);
  free(buf);
  free(sel);
}


struct DualconR
{ node *self;
  struct HonestOTExtSender** s;
};

bool meCsp() { return ocCurrentParty()==1; }
DualconR* dcrConnect(node *self)
{
  int p;
  flush(ocCurrentProto());
  DualconR* dcr = malloc(sizeof*dcr);
  dcr->self = self;
  dcr->s = meCsp()?malloc(sizeof(struct HonestOTExtSender*)*self->num_parties):0;
  if(meCsp()) for(p=0;p<self->num_parties-2;++p)
    dcr->s[p] = honestOTExtSenderNew(self->peer[p+2],0);
  return dcr;
}

void dcrClose(DualconR* dcr)
{
  int p;
  for(p=0;p<dcr->self->num_parties-2;++p)
  {
    if(dcr->s) honestOTExtSenderRelease(dcr->s[p]);
  }
  free(dcr->s); free(dcr);
}

void dcrRecvBitArray(DualconR* dcr,OblivBit* dest,size_t n,int p)
{
  YaoProtocolDesc* ypd = ocCurrentProto()->extra;
  if(!meCsp()) // I am "evaluator"
  { char* buf = malloc(YAO_KEY_BYTES*n);
    orecv(dcr->self->peer[p-1],0,buf,n*YAO_KEY_BYTES);
    int i;
    for(i=0;i<n;++i)
    { yaoKeyCopy(dest[i].yao.w,buf+i*YAO_KEY_BYTES);
      dest[i].unknown=true;
      dest[i].yao.inverted=false;
      ypd->icount++;
    }
    free(buf);
  }
  else // I am CSP
  { char *buf0 = malloc(YAO_KEY_BYTES*n);
    char *buf1 = malloc(YAO_KEY_BYTES*n);
    yao_key_t w0,w1;
    int i;
    for(i=0;i<n;++i)
    { yaoKeyNewPair(ypd,w0,w1); // does ypd->icount++
      yaoKeyCopy(buf0+YAO_KEY_BYTES*i,w0);
      yaoKeyCopy(buf1+YAO_KEY_BYTES*i,w1);
      dest[i].unknown=true; dest[i].yao.inverted=false;
      yaoKeyCopy(dest[i].yao.w,w0);
    }
    honestOTExtSend1Of2(dcr->s[p-3],buf0,buf1,n,YAO_KEY_BYTES);
    flush(dcr->self->peer[p-1]);
    free(buf0);
    free(buf1);
  }
}
