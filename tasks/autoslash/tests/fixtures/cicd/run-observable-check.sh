#!/bin/sh
set -eu
exec python3 "$(dirname "$0")/t3_observable.py" "$@"
