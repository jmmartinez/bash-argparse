#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "str my_name" \
              -- $@ )

eval ${ARG_VARS}
echo "my name is:" ${MY_NAME}
