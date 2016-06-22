#include<obliv.h>
#include<stdio.h>
#include<stdlib.h>
#include<time.h>
#include <errno.h>
#include <arpa/inet.h>

#include"util.h"

#ifndef REMOTE_HOST
#define REMOTE_HOST localhost
#endif

#define QUOTE(x) #x
#define TO_STRING(x) QUOTE(x)
static const char remote_host[] = TO_STRING(REMOTE_HOST);
#undef TO_STRING
#undef QUOTE

double wallClock() {
	struct timespec t;
	clock_gettime(CLOCK_REALTIME,&t);
	return t.tv_sec+1e-9*t.tv_nsec;
}

const struct timespec sleeptime = {.tv_nsec = 200000000};

void util_loop_accept(ProtocolDesc *pd, const char *port) {
	while(protocolAcceptTcp2P(pd,port)!=0) {
		nanosleep(&sleeptime, NULL);
	}
}

void util_loop_connect(ProtocolDesc *pd, const char *host, const char *port) {
	while(protocolConnectTcp2P(pd,host,port)!=0) { 
		nanosleep(&sleeptime, NULL);
	}
}


void ocTestUtilTcpOrDie(ProtocolDesc* pd,bool isServer,const char* port) {
	if(isServer) { 
		util_loop_accept(pd, port);
	} else{
		util_loop_connect(pd, remote_host, port);
	}
}

const char *get_remote_host() {
	return remote_host;
}

// stolen from obliv_bits.c
int tcpListenAny(const char* portn) {
	in_port_t port;
	int outsock;
	if(sscanf(portn,"%hu",&port)<1) return -1;
	if((outsock=socket(AF_INET,SOCK_STREAM,0))<0) return -1;
	int reuse = 1;
	if (setsockopt(outsock, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse)) < 0) {
		fprintf(stderr,"setsockopt(SO_REUSEADDR) failed\n"); 
		return -1;
	}
	struct sockaddr_in sa = { 
		.sin_family=AF_INET, 
		.sin_port=htons(port),
		.sin_addr={INADDR_ANY} 
	};
	if(bind(outsock,(struct sockaddr*)&sa,sizeof(sa))<0) return -1;
	if(listen(outsock,SOMAXCONN)<0) return -1;
	return outsock;
}
