#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.bookshop_browser_laws "$@"
