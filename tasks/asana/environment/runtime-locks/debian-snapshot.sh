#!/bin/sh
# Immutable Debian repositories; retain Release signature verification.
set -eu
. /etc/os-release
[ "$ID:$VERSION_CODENAME" = "debian:bookworm" ] || { echo "Expected Debian bookworm" >&2; exit 1; }
# Replace both legacy and deb822 sources so no moving mirror can participate.
rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources
cat > /etc/apt/sources.list.d/websitebench.sources <<'EOF'
Types: deb
URIs: https://snapshot.debian.org/archive/debian/20260901T000000Z/
Suites: bookworm bookworm-updates
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
Check-Valid-Until: no

Types: deb
URIs: https://snapshot.debian.org/archive/debian-security/20260901T000000Z/
Suites: bookworm-security
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
Check-Valid-Until: no
EOF
cat > /etc/apt/apt.conf.d/80websitebench-retries <<'EOF'
Acquire::Retries "5";
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";
EOF
