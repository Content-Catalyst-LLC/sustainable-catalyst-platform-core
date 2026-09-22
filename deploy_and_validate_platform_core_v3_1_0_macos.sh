#!/usr/bin/env bash
set -euo pipefail
ARCHIVE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v3.1.0-repository.zip}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/PUSH_PLATFORM_CORE_V3100_FINAL.sh" "$ARCHIVE"
