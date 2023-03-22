#!/usr/bin/env bash
set -eou pipefail

readonly WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${WORKDIR}/test > /dev/null
bash bool.sh | grep "boolean is: false"
bash bool.sh --boolean | grep "boolean is: true"
bash bool.sh --no-boolean | grep "boolean is: false"
bash int.sh | grep "count is: 0"
bash int.sh --count=1 | grep "count is: 1"
bash int.sh --count=2 | grep "count is: 2"
bash string.sh --my-name=jmmartinez | grep "my name is: jmmartinez"
bash string.sh --my-name="Juan Manuel" | grep "my name is: Juan Manuel"
bash list.sh --shop apple --shop banana --shop orange | grep "shopping list: apple banana orange"
bash varargs.sh --my-name=jmmartinez | grep "my name is: jmmartinez"
bash varargs.sh --my-name=jmmartinez -- a b c | grep "my name is: jmmartinez"
bash varargs.sh --my-name=jmmartinez -- a b c | grep "remaining args: a b c"
bash dash.sh --dash-count=2 | grep "count is: 2"

( bash help_on_empty.sh 2>&1 || true ) | grep "usage"

bash readme.sh --get-src --compile --run | grep "Hello World!"
rm -f hello.cpp a.out

popd > /dev/null
echo ""
echo "Test ok!"
