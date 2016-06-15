#pragma once

#include <czmq.h>
#include "obliv.h"

int protocol_use_zsock(ProtocolDesc *pd, zsock_t *socket);
