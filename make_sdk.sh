#!/bin/zsh

SDK_PATH="$(cd "$(dirname "$0")" && pwd)/Framework"
export DYLD_FRAMEWORK_PATH="$SDK_PATH"
make
MAKE_STATUS=$?

if [[ $MAKE_STATUS -ne 0 ]]; then
  echo " Build failed running the make file. Exiting."
  return 1
fi
