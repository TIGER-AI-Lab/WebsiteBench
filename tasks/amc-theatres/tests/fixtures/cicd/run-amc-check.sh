#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.amc_semantic_check "$@"
