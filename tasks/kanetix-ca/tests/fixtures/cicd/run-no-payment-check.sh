#!/usr/bin/env sh
set -eu

run_trusted_check() {
  python="$(command -v python3 || command -v python)"
  "$python" -m websitebench.harbor.trusted_check "$@"
}

run_trusted_check "$@"
run_trusted_check \
  --site kanetix-ca \
  --contract cicd/obligations.json \
  --assertion logs-and-artifacts-contain-no-secret-values
