OBLIVCC=$(OBLIVC_PATH)/bin/oblivcc
REMOTE_HOST=localhost

binDir=bin
objDir=obj
srcDir=src
libDir=lib

ackLibDir=$(libDir)/absentminded-crypto-kit/build/lib
ackLib=$(ackLibDir)/liback.a
ackIncDir=$(libDir)/absentminded-crypto-kit/src/
LFLAGS += -L$(ackLibDir) -lack
CFLAGS += -g -DREMOTE_HOST=$(REMOTE_HOST) -O3 -Werror -I$(ackIncDir)

compile=mkdir -p $(@D) && $(OBLIVCC) $(CFLAGS) -c -I $(srcDir) $^ -o $@
link=mkdir -p $(@D) && $(OBLIVCC) $(LFLAGS) $^ -o $@

native=$(objDir)/$(1)_c.o
obliv=$(objDir)/$(1)_o.o
both=$(call native,$(1)) $(call obliv,$(1))

$(binDir)/test_linear_system: $(ackLib) $(call native,test/test_linear_system) $(call both,linear) $(call both,fixed) $(call native,util) $(call obliv,ldlt) $(call obliv,cholesky) $(call obliv,cgd)
	$(link)

$(binDir)/test_fixed: $(ackLib) $(call both,test/test_fixed) $(call both,fixed) $(call native,util)
	$(link)

$(ackLib):
	cd $(libDir)/absentminded-crypto-kit && make

$(objDir)/%_c.o: $(srcDir)/%.c
	$(compile)

$(objDir)/%_o.o: $(srcDir)/%.oc
	$(compile)

clean:
	rm -rf $(binDir) $(objDir)
	cd $(libDir)/absentminded-crypto-kit && make clean
