#!/bin/bash
# REQUIRES: linux

# RUN: export PYTHON_EXEC="%{python}"
# RUN: export BASH_ARGPARSE_PY="%{bash-argparse-script}"
#
# RUN: bash %s | %{FileCheck} %s
# RUN: bash -x %s | %{FileCheck} %s
# RUN: bash %s toto.sh | %{FileCheck} %s
# RUN: /bin/bash %s | %{FileCheck} %s
# RUN: %s | %{FileCheck} %s

set -e

# do an || true to ensure the script doesn't stop after printing the help message
${PYTHON_EXEC} ${BASH_ARGPARSE_PY} --signature "int option" -- --help 2>&1 \
    || true

# The deduced name of the program is the name of the script
# CHECK: usage: deduce_program_bash.sh
