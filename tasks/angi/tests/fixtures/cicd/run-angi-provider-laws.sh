#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.angi_provider_laws "$@"
