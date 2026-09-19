#!/bin/bash
# Install this checkout into the selected existing Hermes home; do not replace bots.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$REPO_ROOT/tools/install_hermes_skills.py" --repo "$REPO_ROOT" "$@"
