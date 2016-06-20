#include<obliv.h>
#include<stdio.h>
#include<stdlib.h>
#include<time.h>
#include"util.h"
#include <errno.h>

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
