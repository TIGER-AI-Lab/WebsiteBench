#!/usr/bin/env sh
set -eu
exec python3 -m websitebench.harbor.change_campaign_laws "$@"
