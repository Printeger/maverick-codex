#!/usr/bin/env bash
set -euo pipefail

forge_python="${FORGE_PYTHON:-python3}"
"$forge_python" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or newer is required"'

# FORGE_SOURCE supports an existing checkout and offline installation tests.
if [[ -n "${FORGE_SOURCE:-}" ]]; then
  exec "$forge_python" "$FORGE_SOURCE/scripts/forge.py" install "$@"
fi

forge_temp="$(mktemp -d)"
trap 'rm -rf "$forge_temp"' EXIT
curl -fsSL 'https://github.com/Printeger/maverick-codex/archive/refs/heads/maverick-forge.tar.gz' -o "$forge_temp/source.tar.gz"
tar -xzf "$forge_temp/source.tar.gz" -C "$forge_temp"
forge_source="$forge_temp/maverick-codex-maverick-forge"
"$forge_python" "$forge_source/scripts/forge.py" install "$@"
