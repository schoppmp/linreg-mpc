OBLIVCC=$(OBLIVC_PATH)/bin/oblivcc

binDir=bin
objDir=obj
srcDir=src
libDir=lib

REMOTE_HOST=localhost
BIT_WIDTH_32=0
CFLAGS=-O3 -g -Werror -I $(srcDir) -I $(OBLIVC_PATH)/src/ext/oblivc -std=c11 -D_POSIX_C_SOURCE=201605L -DBIT_WIDTH_32=$(BIT_WIDTH_32)
LFLAGS=-L$(HOME)/lib
OCFLAGS=$(CFLAGS) -DREMOTE_HOST=$(REMOTE_HOST)

ackLibDir=$(libDir)/absentminded-crypto-kit/build/lib
ackLib=$(ackLibDir)/liback.a
ackIncDir=$(libDir)/absentminded-crypto-kit/src/
OLFLAGS += -L$(ackLibDir) -lack
OCFLAGS += -g -DREMOTE_HOST=$(REMOTE_HOST) -O3 -Werror -I$(ackIncDir)

mkpath=mkdir -p $(@D)
compile=$(mkpath) && $(CC) $(CFLAGS) -c $< -o $@
link=$(mkpath) && $(CC) $(LFLAGS) $^ -o $@
compile_obliv=$(mkpath) && $(OBLIVCC) $(OCFLAGS) -c $< -o $@
link_obliv=$(mkpath) && $(OBLIVCC) $(OLFLAGS) $^ -o $@

native=$(objDir)/$(1)_c.o
obliv=$(objDir)/$(1)_o.o
both=$(call native,$(1)) $(call obliv,$(1))

# all: $(binDir)/test_multiplication $(binDir)/test_linear_system $(binDir)/test_inner_product $(binDir)/secure_multiplication $(binDir)/main $(binDir)/test_fixed
all: $(binDir)/test_linear_system $(binDir)/secure_multiplication $(binDir)/main $(binDir)/test_fixed

$(binDir)/main: $(objDir)/main.o $(objDir)/secure_multiplication/node.o $(objDir)/secure_multiplication/config.o $(objDir)/secure_multiplication/phase1.o $(objDir)/secure_multiplication/secure_multiplication.pb-c.o $(call both,linear) $(call both,fixed) $(call native,util) $(call obliv,ldlt) $(call obliv,cholesky) $(call obliv,cgd) $(call native,input)
	$(link_obliv) -lprotobuf-c -lm

$(binDir)/secure_multiplication:$(objDir)/secure_multiplication/secure_multiplication.pb-c.o $(objDir)/secure_multiplication/secure_multiplication.o $(objDir)/secure_multiplication/config.o $(objDir)/secure_multiplication/node.o $(objDir)/linear.o $(objDir)/fixed.o $(objDir)/secure_multiplication/phase1.o $(objDir)/util.o
	$(link_obliv) -lprotobuf-c -lm

$(binDir)/test_inner_product: $(objDir)/test/test_inner_product.pb-c.o $(objDir)/test/test_inner_product.o $(objDir)/fixed.o $(objDir)/linear.o
	$(link) -lzmq -lprotobuf-c -lgcrypt

$(binDir)/test_multiplication: $(objDir)/test/test_multiplication.pb-c.o $(objDir)/test/test_multiplication.o $(objDir)/fixed.o
	$(link) -lzmq -lprotobuf-c -lgcrypt

$(binDir)/test_linear_system: $(ackLib) $(call native,test/test_linear_system) $(call both,linear) $(call both,fixed) $(call native,util) $(call obliv,ldlt) $(call obliv,cholesky) $(call obliv,cgd) $(call native,input)
	$(link_obliv)

$(binDir)/test_fixed: $(call both,test/test_fixed) $(call both,fixed) $(call native,util)
	$(link_obliv)

$(binDir)/test_input: $(call native,input) $(call obliv,test/test_input) $(call native,util)
	$(link_obliv)

$(ackLib):
	cd $(libDir)/absentminded-crypto-kit && make

$(objDir)/%_c.o: $(srcDir)/%.c
	$(compile_obliv)

$(objDir)/%_o.o: $(srcDir)/%.oc
	$(compile_obliv)

$(objDir)/%.o: $(srcDir)/%.c
	$(compile)

ifeq ($(BIT_WIDTH_32), 1)
$(srcDir)/%.pb-c.c: $(srcDir)/%.proto
	cd $(<D) && protoc-c secure_multiplication_bitwidth_32.proto --c_out=. &&\
	mv secure_multiplication_bitwidth_32.pb-c.c secure_multiplication.pb-c.c &&\
	cp secure_multiplication_bitwidth_32.pb-c.h secure_multiplication.pb-c.h 	
else
$(srcDir)/%.pb-c.c: $(srcDir)/%.proto
	cd $(<D) && protoc-c secure_multiplication_bitwidth_64.proto --c_out=. &&\
	mv secure_multiplication_bitwidth_64.pb-c.c secure_multiplication.pb-c.c &&\
	cp secure_multiplication_bitwidth_64.pb-c.h secure_multiplication.pb-c.h
endif

clean:
	rm -rf $(binDir) $(objDir)
	cd $(libDir)/absentminded-crypto-kit && make clean
