#pragma once

void ocTestUtilTcpOrDie(struct ProtocolDesc* pd,bool isServer,const char* port);
double wallClock();
const char *get_remote_host();

