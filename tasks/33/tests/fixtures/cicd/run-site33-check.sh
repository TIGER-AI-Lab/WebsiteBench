#!/usr/bin/env sh
set -eu
exec python3 "$(dirname "$0")/site33_check.py" "$@"
