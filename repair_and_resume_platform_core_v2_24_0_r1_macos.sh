#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.24.0 R1 repair/resume stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

BUNDLE="${1:-sustainable-catalyst-platform-core-v2.24.0-release-bundle-REPAIRED-R1.zip}"
[ -f "$BUNDLE" ] || { echo "ERROR: Repaired R1 bundle not found: $BUNDLE"; exit 1; }
BUNDLE_DIR="$(cd "$(dirname "$BUNDLE")" && pwd)"
BUNDLE_ABS="${BUNDLE_DIR}/$(basename "$BUNDLE")"
WORK="${TMPDIR:-/tmp}/sc-platform-core-v2240-r1-resume"

for cmd in unzip shasum bash python3; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $cmd"; exit 1; }
done

rm -rf "$WORK"
mkdir -p "$WORK"
unzip -q "$BUNDLE_ABS" -d "$WORK"
cd "$WORK"

[ -f SHA256SUMS.txt ] || { echo "ERROR: R1 SHA256SUMS.txt missing"; exit 1; }
shasum -a 256 -c SHA256SUMS.txt

REPO_ZIP="sustainable-catalyst-platform-core-v2.24.0-repository.zip"
[ -f "$REPO_ZIP" ] || { echo "ERROR: repaired repository ZIP missing"; exit 1; }
[ -f PUSH_PLATFORM_CORE_V2240_FINAL.sh ] || { echo "ERROR: repaired push script missing"; exit 1; }
[ -f deploy_and_validate_platform_core_v2_24_0_macos.sh ] || { echo "ERROR: repaired deploy script missing"; exit 1; }

rm -rf repo-preflight
mkdir repo-preflight
unzip -q "$REPO_ZIP" -d repo-preflight
ROOT="repo-preflight/sustainable-catalyst-platform-core-v2.24.0"
[ -f "$ROOT/scripts/validate_v2240_r1_promotion_repair.py" ] || { echo "ERROR: R1 promotion validator missing"; exit 1; }
(
  cd "$ROOT"
  python3 scripts/validate_v2240_release.py
  python3 scripts/validate_v2240_r1_promotion_repair.py
  python3 scripts/scan_push_safe_secrets.py .
  bash -n PUSH_PLATFORM_CORE_V2240_FINAL.sh
  bash -n deploy_and_validate_platform_core_v2_24_0_macos.sh
  bash -n repair_and_resume_platform_core_v2_24_0_r1_macos.sh
)

echo "PASS - v2.24.0 R1 secret-scan promotion repair preflight"
chmod +x deploy_and_validate_platform_core_v2_24_0_macos.sh
exec ./deploy_and_validate_platform_core_v2_24_0_macos.sh "$BUNDLE_ABS"
