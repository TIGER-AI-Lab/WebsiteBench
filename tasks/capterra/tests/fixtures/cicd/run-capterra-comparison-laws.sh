#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.capterra_comparison_laws "$@"
