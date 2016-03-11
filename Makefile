OBLIVCC=oblivcc
REMOTE_HOST=localhost
CFLAGS=-DREMOTE_HOST=$(REMOTE_HOST) -O3 -Werror
binaryName=solveLS
binDir=bin
srcDir=src


$(binDir)/test_fixed: $(srcDir)/fixed.oc $(srcDir)/fixed.c $(srcDir)/test/test_fixed.c $(srcDir)/test/test_fixed.oc $(srcDir)/util.c
	$(OBLIVCC) $(CFLAGS) -I $(srcDir) $^ -o $@
clean:
	rm -f $(binDir)/test_fixed
