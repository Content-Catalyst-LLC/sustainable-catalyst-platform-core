#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_RUST_RUNTIME_ROOT:-/opt/sustainable-catalyst/rust-runtime}"
DATA_ROOT="${SC_RUST_DATA_ROOT:-/var/lib/sc-rust-runtime}"
EXPECTED_RUSTC_VERSION="${SC_RUSTC_VERSION:-1.75.0}"
EXPECTED_CARGO_VERSION="${SC_CARGO_VERSION:-1.75.0}"
EXPECTED_PACKAGE_VERSION="${SC_RUST_PACKAGE_VERSION:-1.75.0+dfsg0ubuntu1-0ubuntu7.4}"

echo "=== SUSTAINABLE CATALYST RUST RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
RUSTC_CANDIDATE="$(apt-cache policy rustc | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
CARGO_CANDIDATE="$(apt-cache policy cargo | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$RUSTC_CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || { echo "ERROR: expected rustc candidate $EXPECTED_PACKAGE_VERSION, got $RUSTC_CANDIDATE"; exit 1; }
[[ "$CARGO_CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || { echo "ERROR: expected cargo candidate $EXPECTED_PACKAGE_VERSION, got $CARGO_CANDIDATE"; exit 1; }

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "rustc=$EXPECTED_PACKAGE_VERSION" \
  "cargo=$EXPECTED_PACKAGE_VERSION" \
  curl python3-venv rsync

rustc --version
cargo --version
rustc --version | grep -F "rustc $EXPECTED_RUSTC_VERSION" >/dev/null || { echo "ERROR: rustc version mismatch"; exit 1; }
cargo --version | grep -F "cargo $EXPECTED_CARGO_VERSION" >/dev/null || { echo "ERROR: cargo version mismatch"; exit 1; }

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"; sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/rust-runtime-pre-v100-${STAMP}.tar.gz" rust-runtime || true
fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"
cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install 'pytest>=8,<10' >/dev/null

export SC_RUSTC_VERSION="$EXPECTED_RUSTC_VERSION"
export SC_CARGO_VERSION="$EXPECTED_CARGO_VERSION"
export SC_RUST_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION"
export SC_CARGO_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION"
export SC_RUSTC_BIN=/usr/bin/rustc
export SC_CARGO_BIN=/usr/bin/cargo
export SC_RUST_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_RUST_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
RUSTC=/usr/bin/rustc PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_native_kernels.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py validate_native_kernels.py

sudo cp deploy/sc-rust-runtime.service /etc/systemd/system/sc-rust-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-rust-runtime.service >/dev/null
sudo systemctl restart sc-rust-runtime.service
READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18101/health >/dev/null 2>&1; then READY=1; break; fi
  sleep 2
done
if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-rust-runtime.service --no-pager || true
  sudo journalctl -u sc-rust-runtime.service -n 160 --no-pager || true
  exit 1
fi
bash deploy/VERIFY_SC_RUNTIME_RUST_V100.sh

echo "PASS - SUSTAINABLE CATALYST RUST RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
