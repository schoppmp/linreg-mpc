#pragma once

void util_loop_accept(ProtocolDesc *pd, const char *port);
void util_loop_connect(ProtocolDesc *pd, const char *host, const char *port);
void ocTestUtilTcpOrDie(struct ProtocolDesc* pd,bool isServer,const char* port);
double wallClock();
const char *get_remote_host();

