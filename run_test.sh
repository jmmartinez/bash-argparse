#!/usr/bin/env bash
set -eou pipefail

readonly WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${WORKDIR}/test > /dev/null

set -x

bash string.sh --my-name=jmmartinez | grep "my name is: jmmartinez"
bash string.sh --my-name="Juan Manuel" | grep "my name is: Juan Manuel"

bash list.sh --shop apple --shop banana --shop orange | grep "shopping list: apple banana orange"

bash dash.sh --dash-count=2 | grep "count is: 2"

bash unsigned.sh --count=2 | grep "count is: 2"
bash unsigned.sh | grep "count is: 0"
! bash unsigned.sh --count=-1

bash enum.sh | grep "build type is: debug"
bash enum.sh --build-type debug | grep "build type is: debug"
bash enum.sh --build-type release | grep "build type is: release"
! bash enum.sh --build-type house

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

! bash bool_required.sh
bash bool_required.sh --boolean | grep "boolean is: true"
bash bool_required.sh --no-boolean | grep "boolean is: false"

bash output_path.sh | grep "the path is:" | grep test
bash output_path.sh --this-path=$PWD/output.txt | grep "the path is:" | grep test
! bash output_path.sh --this-path=$PWD

( bash help_on_empty.sh 2>&1 || true ) | grep "usage"

bash readme.sh --get-src --compile --run | grep "Hello World!"
set +x
rm -f hello.cpp a.out

popd > /dev/null
echo ""
echo "Test ok!"
