#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "bool get_src; bool compile; bool debug; bool run; bool verbose" \
              --description "The script compiles a program" \
              -- $@ )
eval ${ARG_VARS}

( ! ${VERBOSE} ) || set -x

if ${GET_SRC}; then
  [ -f hello.cpp ] || \
    wget "https://gist.githubusercontent.com/mpcv/0cb7cdfba1a345a1eeb4bcc4f0bed4af/raw/5da7cf8a8037985e8812ddd0f477045068e7fe10/hello.cpp"
fi

if ${COMPILE}; then
  flags="-O2"
  if ${DEBUG}; then
    flags="-g -O0"
  fi
  
  g++ hello.cpp $flags -o a.out
fi

if ${RUN}; then
  if ${DEBUG}; then
    gdb -ex "b main" -ex "r" \
      --args ./a.out
  else
    ./a.out;
  fi
fi

