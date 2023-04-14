#!/usr/bin/env bash
set -eou pipefail

ARG_VARS=$( python3 ../bash-argparse.py \
              --program "${BASH_SOURCE[0]}" \
              --signature "enum<debug,release> build_type" \
              -- "$@" )

eval ${ARG_VARS}
echo "build type is:" ${BUILD_TYPE}
