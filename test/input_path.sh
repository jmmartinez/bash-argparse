#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "input_path this_path=$PWD" \
              -- "$@" )

eval ${ARG_VARS}
echo "the path is: " ${THIS_PATH}
