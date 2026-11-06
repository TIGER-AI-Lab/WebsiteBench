#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.capterra_review_filter_laws "$@"
