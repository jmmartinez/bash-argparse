#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "int count" \
              --prefix "ARGS_" \
              -- "$@" )
eval ${ARG_VARS}
echo "count is:" ${ARGS_COUNT}
