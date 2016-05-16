
binDir=bin
objDir=obj
srcDir=src

OBLIVCC=oblivcc
REMOTE_HOST=localhost
CFLAGS=-O3 -Werror -I $(srcDir)
OCFLAGS=$(CFLAGS) -DREMOTE_HOST=$(REMOTE_HOST)

mkpath=mkdir -p $(@D)
compile=$(mkpath) && $(CC) $(CFLAGS) -c $< -o $@
link=$(mkpath) && $(CC) $(LFLAGS) $^ -o $@
compile_obliv=$(mkpath) && $(OBLIVCC) $(OCFLAGS) -c $< -o $@
link_obliv=$(mkpath) && $(OBLIVCC) $(OLFLAGS) $^ -o $@

native=$(objDir)/$(1)_c.o
obliv=$(objDir)/$(1)_o.o
both=$(call native,$(1)) $(call obliv,$(1))

all: $(binDir)/test_multiplication $(binDir)/test_linear_system $(binDir)/test_inner_product $(binDir)/secure-multiplication

$(binDir)/secure-multiplication: $(objDir)/secure-multiplication/secure-multiplication.o $(objDir)/secure-multiplication/config.o $(objDir)/secure-multiplication/node.o 
	$(link) -lczmq -lzmq

$(binDir)/test_inner_product: $(objDir)/test/test_inner_product.pb-c.o $(objDir)/test/test_inner_product.o $(objDir)/fixed.o $(objDir)/linear.o
	$(link) -lzmq -lprotobuf-c -lgcrypt

$(binDir)/test_multiplication: $(objDir)/test/test_multiplication.pb-c.o $(objDir)/test/test_multiplication.o $(objDir)/fixed.o
	$(link) -lzmq -lprotobuf-c -lgcrypt

$(binDir)/test_linear_system: $(call native,test/test_linear_system) $(call both,linear) $(call both,fixed) $(call native,util) $(call obliv,ldlt) $(call obliv,cholesky) $(call obliv,cgd)
	$(link_obliv)

$(binDir)/test_fixed: $(call both,test/test_fixed) $(call both,fixed) $(call native,util)
	$(link_obliv)

$(objDir)/%_c.o: $(srcDir)/%.c
	$(compile_obliv)

$(objDir)/%_o.o: $(srcDir)/%.oc
	$(compile_obliv)

$(objDir)/%.o: $(srcDir)/%.c
	$(compile)

$(srcDir)/%.pb-c.c: $(srcDir)/%.proto
	cd $(<D) && protoc-c $(<F) --c_out=.

clean:
	rm -rf $(binDir) $(objDir)
