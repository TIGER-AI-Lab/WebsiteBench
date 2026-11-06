#!/usr/bin/env sh
set -eu
python="$(command -v python3 || command -v python)"
exec "$python" -m websitebench.harbor.angi_demo_entry "$@"
