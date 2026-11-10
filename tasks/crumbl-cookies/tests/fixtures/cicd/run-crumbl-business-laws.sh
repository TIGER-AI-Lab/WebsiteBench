#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.crumbl_business_laws "$@"
