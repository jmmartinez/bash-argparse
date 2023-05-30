#!/usr/bin/env bash
set -eou pipefail

readonly WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${WORKDIR}/test > /dev/null

set -x

bash input_path.sh | grep "the path is:" | grep test
bash input_path.sh --this-path=. | grep "the path is:" | grep test
bash input_path.sh --this-path=$PWD | grep "the path is:" | grep test
! bash input_path.sh --this-path=${PWD}_fail

bash output_path.sh | grep "the path is:" | grep test
bash output_path.sh --this-path=$PWD/output.txt | grep "the path is:" | grep test
! bash output_path.sh --this-path=$PWD

set +x

popd > /dev/null
echo ""
echo "Test ok!"
