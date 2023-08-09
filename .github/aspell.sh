#!/bin/bash
set -eou pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

error() {
  echo $1
  exit 1 
}

require() {
  $1 -v &> /dev/null || error "$1 not found"
}

require aspell

pushd ${SCRIPT_DIR} > /dev/null

ASPELL_HOME=$PWD/aspell
[ -d $ASPELL_HOME ] || error "Could not find .github/aspell directory"

LOG=$(mktemp).log

trap "rm -f $LOG" EXIT

touch $LOG

FAIL=false
FILES=$(find .. -iname "*.md" | sort)
for file in $FILES; do
  echo "# Spellcheck on $file" >> $LOG
  WORD_LIST=$(cat $file | aspell --lang=en --mode=markdown --home-dir=$ASPELL_HOME list) 
  
  if [[ ! -z $WORD_LIST ]]; then
    echo $WORD_LIST >> $LOG
    FAIL=true
  fi
  echo "" >> $LOG
done

if $FAIL; then
  cat $LOG

  error "Errors found!"
fi
popd > /dev/null
