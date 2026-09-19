#!/bin/bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${ZION_RUNTIME_CONFIG:?Set ZION_RUNTIME_CONFIG to the private runtime JSON path}"
exec python3 "$REPO_ROOT/tools/zion_deploy.py" --config "$ZION_RUNTIME_CONFIG" start
