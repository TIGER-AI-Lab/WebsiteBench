#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.beeradvocate_member_laws "$@"
