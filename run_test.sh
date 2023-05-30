#!/usr/bin/env bash
set -eou pipefail

readonly WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${WORKDIR}/test > /dev/null

set -x

bash input_path.sh | grep "the path is:" | grep test
bash input_path.sh --this-path=. | grep "the path is:" | grep test
bash input_path.sh --this-path=$PWD | grep "the path is:" | grep test
! bash input_path.sh --this-path=${PWD}_fail

bash positional.sh a b | grep "positional: a b"
bash positional.sh a b | grep "optional: ahoy"
bash positional.sh a b --optional c | grep "positional: a b"
bash positional.sh a b --optional c | grep "optional: c"
bash positional.sh a --optional c b | grep "positional: a b"
bash positional.sh a --optional c b | grep "optional: c"
! bash positional.sh
! bash positional.sh a

bash output_path.sh | grep "the path is:" | grep test
bash output_path.sh --this-path=$PWD/output.txt | grep "the path is:" | grep test
! bash output_path.sh --this-path=$PWD

bash readme.sh --get-src --compile --run | grep "Hello World!"
set +x
rm -f hello.cpp a.out

popd > /dev/null
echo ""
echo "Test ok!"
