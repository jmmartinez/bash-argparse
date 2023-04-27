#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "str @first; str @second; str optional=ahoy" \
              -- "$@" )

eval ${ARG_VARS}
echo "positional:" ${FIRST} ${SECOND}
echo "optional:" ${OPTIONAL}
