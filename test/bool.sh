#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "bool boolean" \
              -- $@ )
eval ${ARG_VARS}
echo "boolean is:" ${BOOLEAN}
