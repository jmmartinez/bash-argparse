#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "int dash_count" \
              -- "$@" )
eval ${ARG_VARS}
echo "count is:" ${DASH_COUNT}
