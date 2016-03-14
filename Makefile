OBLIVCC=oblivcc
REMOTE_HOST=localhost
CFLAGS=-DREMOTE_HOST=$(REMOTE_HOST) -O3 -Werror

binDir=bin
objDir=obj
srcDir=src

compile_c=mkdir -p $(@D) && $(CC) $(CFLAGS) -c -I /usr/include/oblivc -I $(srcDir) $^ -o $@
compile_o=mkdir -p $(@D) && $(OBLIVCC) $(CFLAGS) -c -I $(srcDir) $^ -o $@
link=mkdir -p $(@D) && $(OBLIVCC) $(LFLAGS) $^ -o $@

native=$(objDir)/$(1)_c.o
obliv=$(objDir)/$(1)_o.o
both=$(call native,$(1)) $(call obliv,$(1))

$(binDir)/test_cholesky: $(call native,test/test_cholesky) $(call obliv,linear) $(call both,fixed) $(call native,util) $(call obliv,cholesky)
	$(link)

$(binDir)/test_fixed: $(call both,test/test_fixed) $(call both,fixed) $(call native,util)
	$(link)

$(objDir)/%_c.o: $(srcDir)/%.c
	$(compile_c)

$(objDir)/%_o.o: $(srcDir)/%.oc
	$(compile_o)

clean:
	rm -rf $(binDir) $(objDir)
