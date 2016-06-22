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

struct DualconS
{ ProtocolDesc pd1,pd2; 
  struct HonestOTExtRecver* r; 
};
static void flush(ProtocolDesc* pd)
{
  orecv(pd,0,NULL,0); // hack that causes two parties to flush
}
DualconS* dcsConnect(const char* csp_server,const char* csp_port,
                     const char* eval_server,const char* eval_port,
                     int party)
{
  DualconS* dcs = malloc(sizeof(*dcs));
  dhRandomInit();
  // Not setting party numbers: problem? check
  // Zeroes everywhere: Tcp2P ignores party numbers anyway
  util_loop_connect(&dcs->pd1,csp_server,csp_port);
//  if(protocolConnectTcp2P(&dcs->pd1,csp_server,csp_port)!=0)
//    error(-1,errno,"Could not connect to %s:%s",csp_server,csp_port);
  osend(&dcs->pd1,0,&party,sizeof(party));
  util_loop_connect(&dcs->pd2,eval_server,eval_port);
//  if(protocolConnectTcp2P(&dcs->pd2,eval_server,eval_port)!=0)
//    error(-1,errno,"Could not connect to %s:%s",eval_server,eval_port);
  osend(&dcs->pd2,0,&party,sizeof(party));
  flush(&dcs->pd2);
  dcs->r = honestOTExtRecverNew(&dcs->pd1,0);
  return dcs;
}
void dcsClose(DualconS* dcs)
{
  honestOTExtRecverRelease(dcs->r);
  cleanupProtocol(&dcs->pd1);
  cleanupProtocol(&dcs->pd2);
  free(dcs);
}
static const int intsize = 64;
void dcsSendIntArray(DualconS* dcs,const uint64_t* input,int n)
{
  int i,j,nn = n*intsize;
  bool* sel = malloc(nn*sizeof(bool));
  char* buf = malloc(nn*YAO_KEY_BYTES);
  for(i=0;i<n;++i) for(j=0;j<intsize;++j) sel[i*intsize+j]=((input[i]>>j)&1);
  honestOTExtRecv1Of2(dcs->r,buf,sel,nn,YAO_KEY_BYTES);
  osend(&dcs->pd2,0,buf,nn*YAO_KEY_BYTES);
  free(buf);
  free(sel);
}


struct DualconR
{ ProtocolDesc *pd; 
  int count,*party; 
  struct HonestOTExtSender** s;
};

bool meCsp() { return ocCurrentParty()==1; }
DualconR* dcrConnect(const char* port,int pc)
{
  int p;
  flush(ocCurrentProto());
  DualconR* dcr = malloc(sizeof*dcr);
  dcr->pd = malloc(sizeof(ProtocolDesc)*pc);
  dcr->count = pc;
  dcr->party = malloc(sizeof(int)*pc);
  dcr->s = meCsp()?malloc(sizeof(struct HonestOTExtSender*)*pc):0;
  int listen_socket = tcpListenAny(port);
  for(p=0;p<pc;++p) {
    int sock=accept(listen_socket,0,0);
    protocolUseTcp2P(dcr->pd+p,sock,false);
//  { if(protocolAcceptTcp2P(dcr->pd+p,port)!=0)
//      error(-1,errno,"TCP connection error");
    orecv(dcr->pd+p,0,dcr->party+p,sizeof(int));
  }
  close(listen_socket);
  if(meCsp()) for(p=0;p<pc;++p)
    dcr->s[p] = honestOTExtSenderNew(dcr->pd+p,0);
  return dcr;
}

void dcrClose(DualconR* dcr)
{
  int p;
  for(p=0;p<dcr->count;++p)
  { cleanupProtocol(dcr->pd+p);
    if(dcr->s) honestOTExtSenderRelease(dcr->s[p]);
  }
  free(dcr->s); free(dcr->party); free(dcr->pd); free(dcr);
}
static int partyIndex(DualconR* dcr,int party)
{ int p;
  for(p=0;p<dcr->count;++p) {
	printf("Party: %d, Socket: %d\n", party, dcr->party[p]);
	if(party==dcr->party[p]) {
		return p;
	}
  }
  printf("Failed lookup for party %d\n", p);
  assert(false);
  return -1;
}
void dcrRecvBitArray(DualconR* dcr,OblivBit* dest,int n,int party)
{
  YaoProtocolDesc* ypd = ocCurrentProto()->extra;
  if(!meCsp()) // I am "evaluator"
  { char* buf = malloc(YAO_KEY_BYTES*n);
    int i,p = partyIndex(dcr,party);
    orecv(dcr->pd+p,0,buf,n*YAO_KEY_BYTES);
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
    int i,p = partyIndex(dcr,party);
    for(i=0;i<n;++i)
    { yaoKeyNewPair(ypd,w0,w1); // does ypd->icount++
      yaoKeyCopy(buf0+YAO_KEY_BYTES*i,w0);
      yaoKeyCopy(buf1+YAO_KEY_BYTES*i,w1);
      dest[i].unknown=true; dest[i].yao.inverted=false;
      yaoKeyCopy(dest[i].yao.w,w0);
    }
    honestOTExtSend1Of2(dcr->s[p],buf0,buf1,n,YAO_KEY_BYTES);
    free(buf0);
    free(buf1);
  }
}
