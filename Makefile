OBLIVCC=$(OBLIVC_PATH)/bin/oblivcc

BINDIR=bin
SRCDIR=src
LIBDIR=lib

REMOTE_HOST=localhost
BIT_WIDTH_32_P1=0
BIT_WIDTH_32_P2=0

SOURCES := $(shell find -L $(SRCDIR) -type f -name '*.c' -not -path '*/cmd/*' )
OBJECTS := $(patsubst %.c, %.o, $(SOURCES))
SOURCES_OBLIVC := $(shell find -L $(SRCDIR) -type f -name '*.oc')
OBJECTS_OBLIVC := $(patsubst %.oc, %.oo, $(SOURCES_OBLIVC))
SOURCES_BIN := $(shell find -L $(SRCDIR)/cmd -type f -name '*.c')
OBJECTS_BIN := $(patsubst %.c, %.o, $(SOURCES_BIN))
BINARIES = $(patsubst $(SRCDIR)/cmd/%.c, $(BINDIR)/%, $(SOURCES_BIN))

CFLAGS=-O3 -g -Werror -pthread -I$(SRCDIR) -I$(OBLIVC_PATH)/src/ext/oblivc -std=c11 -D_POSIX_C_SOURCE=201605L -DBIT_WIDTH_32_P1=$(BIT_WIDTH_32_P1) -DBIT_WIDTH_32_P2=$(BIT_WIDTH_32_P2)
LDFLAGS= -lm -lgcrypt -lprotobuf-c
OCFLAGS=$(CFLAGS) -DREMOTE_HOST=$(REMOTE_HOST)

# Absentminded Crypto Kit
ACKLIBDIR=$(LIBDIR)/absentminded-crypto-kit/build/lib
ACKLIB=$(ACKLIBDIR)/liback.a
LDFLAGS += -L$(ACKLIBDIR) -L$(OBLIVC_PATH)/_build -lack -lobliv
OCFLAGS += -I$(LIBDIR)/absentminded-crypto-kit/src/ -D_Float128=double -Dopenssl_noreturn=""

all: $(BINARIES)

# Libraries
$(ACKLIB): $(LIBDIR)/absentminded-crypto-kit/Makefile
	CFLAGS=-D_Float128=double make -C $(LIBDIR)/absentminded-crypto-kit
$(LIBDIR)/absentminded-crypto-kit/Makefile:
	git submodule update --init

# Protocol Buffers
PROTOBUF_PROTOS = $(SRCDIR)/protobuf/secure_multiplication.proto
PROTOBUF_HEADERS = $(PROTOBUF_PROTOS:.proto=.pb-c.h)
PROTOBUF_OBJECTS = $(PROTOBUF_HEADERS:.h=.o)
PROTOBUF_ALL = $(PROTOBUF_PROTOS) $(PROTOBUF_HEADERS) $(PROTOBUF_OBJECTS) $(PROTOBUF_HEADERS:.h=.{c,d})
ifeq ($(BIT_WIDTH_32_P1), 1)
BIT_WIDTH_P1 = 32
else
BIT_WIDTH_P1 = 64
endif
%.proto: %.bitwidth_$(BIT_WIDTH_P1).proto
	cp $< $@
%.pb-c.c %.pb-c.h: %.proto
	cd $(@D) && protoc-c $(<F) --c_out=.

# Dependencies
-include $(SOURCES:.c=.d)
-include $(SOURCES_BIN:.c=.d)
-include $(SOURCES_OBLIVC:.oc=.od)

# do not delete intermediate objects
.SECONDARY: $(OBJECTS) $(OBJECTS_BIN) $(OBJECTS_OBLIVC) $(PROTOBUF_ALL)

# Binaries
$(BINDIR)/%: $(OBJECTS) $(OBJECTS_OBLIVC) $(SRCDIR)/cmd/%.o  $(PROTOBUF_OBJECTS) | $(ACKLIB)
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# C sources
%.o: %.c $(PROTOBUF_HEADERS)
	$(CC) $(CFLAGS) -o $@ -c $<
	$(CC) -MM $(CFLAGS) -MT "$*.o $@" $< > $*.d;
# Obliv-C Sources
%.oo : %.oc
	$(OBLIVCC) $(OCFLAGS) -o $@ -c $<
	$(OBLIVCC) -MM $(OCFLAGS) -MT "$*.oo $@" $< > $*.od;

.PHONY: clean cleanall
clean:
	$(RM) -r $(BINDIR)
	$(RM) $(OBJECTS) $(OBJECTS_BIN) $(OBJECTS_OBLIVC) $(OBJECTS_PROTOBUF)
	$(RM) $(OBJECTS:.o=.d) $(OBJECTS_BIN:.o=.d) $(OBJECTS_OBLIVC:.oo=.od)
	$(RM) $(PROTOBUF_ALL)

cleanall: clean
	cd $(LIBDIR)/absentminded-crypto-kit && make clean
