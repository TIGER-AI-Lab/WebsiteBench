#!/usr/bin/env bash
set -Eeuo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
test -x "$root/executable" || "$root/compile.sh"
exec "$root/executable"
