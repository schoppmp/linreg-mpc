FROM archlinux/base

# base-devel group and git.
RUN pacman --noconfirm -Sy \
  base-devel git

# OPAM for Obliv-C.
RUN pacman --noconfirm -Sy \
  ocaml ocaml-findlib opam
RUN opam init --disable-sandboxing -y --compiler 4.06.0; \
  eval `opam config env`; \
  opam install -y camlp4 ocamlfind ocamlbuild batteries;

# Protobuf-C for linreg-mpc.
RUN pacman --noconfirm -Sy \
  protobuf-c

# Install Obliv-C.
RUN eval $(opam config env); \
  git clone https://github.com/samee/obliv-c.git root/obliv-c; \
  cd /root/obliv-c; \
  ./configure && make

WORKDIR root/linreg-mpc

# Copy Sources and build linreg-mpc.
COPY . .
RUN  eval $(opam config env); \
  export OBLIVC_PATH=/root/obliv-c; \
  make
