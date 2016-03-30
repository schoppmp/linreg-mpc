OBLIVCC=oblivcc
REMOTE_HOST=localhost
CFLAGS=-DREMOTE_HOST=$(REMOTE_HOST) -O3 -Werror

binDir=bin
objDir=obj
srcDir=src

compile=mkdir -p $(@D) && $(OBLIVCC) $(CFLAGS) -c -I $(srcDir) $^ -o $@
link=mkdir -p $(@D) && $(OBLIVCC) $(LFLAGS) $^ -o $@

native=$(objDir)/$(1)_c.o
obliv=$(objDir)/$(1)_o.o
both=$(call native,$(1)) $(call obliv,$(1))

$(binDir)/test_linear_system: $(call native,test/test_linear_system) $(call both,linear) $(call both,fixed) $(call native,util) $(call obliv,ldlt) $(call obliv,cholesky)
	$(link)

$(binDir)/test_fixed: $(call both,test/test_fixed) $(call both,fixed) $(call native,util)
	$(link)

$(objDir)/%_c.o: $(srcDir)/%.c
	$(compile)

$(objDir)/%_o.o: $(srcDir)/%.oc
	$(compile)

clean:
	rm -rf $(binDir) $(objDir)
