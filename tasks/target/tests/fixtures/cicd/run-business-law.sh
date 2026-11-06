#!/usr/bin/env sh
set -eu
if command -v python3 >/dev/null 2>&1; then
    python_bin=python3
else
    python_bin=python
fi
exec "$python_bin" -m websitebench.harbor.target_business_laws "$@"
