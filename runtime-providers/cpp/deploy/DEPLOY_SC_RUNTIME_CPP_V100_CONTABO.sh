#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_CPP_RUNTIME_ROOT:-/opt/sustainable-catalyst/cpp-runtime}"
DATA_ROOT="${SC_CPP_DATA_ROOT:-/var/lib/sc-cpp-runtime}"
EXPECTED_VERSION="${SC_CPP_COMPILER_VERSION:-13.3.0}"
EXPECTED_PACKAGE="${SC_CPP_PACKAGE_VERSION:-13.3.0-6ubuntu2~24.04.1}"

echo "=== SUSTAINABLE CATALYST C/C++ RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
GCC_CANDIDATE="$(apt-cache policy gcc-13 | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
GPP_CANDIDATE="$(apt-cache policy g++-13 | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$GCC_CANDIDATE" == "$EXPECTED_PACKAGE" ]] || { echo "ERROR: expected gcc-13 candidate $EXPECTED_PACKAGE, got $GCC_CANDIDATE"; exit 1; }
[[ "$GPP_CANDIDATE" == "$EXPECTED_PACKAGE" ]] || { echo "ERROR: expected g++-13 candidate $EXPECTED_PACKAGE, got $GPP_CANDIDATE"; exit 1; }

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "gcc-13=$EXPECTED_PACKAGE" \
  "g++-13=$EXPECTED_PACKAGE" \
  curl python3-venv rsync

[[ "$(gcc-13 -dumpfullversion)" == "$EXPECTED_VERSION" ]] || { echo "ERROR: gcc-13 version mismatch"; exit 1; }
[[ "$(g++-13 -dumpfullversion)" == "$EXPECTED_VERSION" ]] || { echo "ERROR: g++-13 version mismatch"; exit 1; }

echo "gcc-13 $(gcc-13 -dumpfullversion)"
echo "g++-13 $(g++-13 -dumpfullversion)"

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/cpp-runtime-pre-v100-${STAMP}.tar.gz" cpp-runtime || true
fi

sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"

cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install 'pytest>=8,<10' >/dev/null

export SC_CPP_GCC_VERSION="$EXPECTED_VERSION"
export SC_CPP_GPP_VERSION="$EXPECTED_VERSION"
export SC_CPP_GCC_PACKAGE_VERSION="$EXPECTED_PACKAGE"
export SC_CPP_GPP_PACKAGE_VERSION="$EXPECTED_PACKAGE"
export SC_CPP_GCC_BIN=/usr/bin/gcc-13
export SC_CPP_GPP_BIN=/usr/bin/g++-13
export SC_CPP_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_CPP_WORK_ROOT="$DATA_ROOT/work"

PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13 PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_native_kernels.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py validate_native_kernels.py

sudo cp deploy/sc-cpp-runtime.service /etc/systemd/system/sc-cpp-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-cpp-runtime.service >/dev/null
sudo systemctl restart sc-cpp-runtime.service

READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18100/health >/dev/null 2>&1; then READY=1; break; fi
  sleep 2
done
if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-cpp-runtime.service --no-pager || true
  sudo journalctl -u sc-cpp-runtime.service -n 160 --no-pager || true
  exit 1
fi

bash deploy/VERIFY_SC_RUNTIME_CPP_V100.sh

echo "PASS - SUSTAINABLE CATALYST C/C++ RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
