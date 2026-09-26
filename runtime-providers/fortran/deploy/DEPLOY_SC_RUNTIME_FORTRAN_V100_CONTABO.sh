#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_FORTRAN_RUNTIME_ROOT:-/opt/sustainable-catalyst/fortran-runtime}"
DATA_ROOT="${SC_FORTRAN_DATA_ROOT:-/var/lib/sc-fortran-runtime}"
EXPECTED_VERSION="${SC_FORTRAN_GFORTRAN_VERSION:-13.3.0}"
EXPECTED_PACKAGE_VERSION="${SC_FORTRAN_GFORTRAN_PACKAGE_VERSION:-13.3.0-6ubuntu2~24.04.1}"

echo "=== SUSTAINABLE CATALYST FORTRAN RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
CANDIDATE="$(apt-cache policy gfortran-13 | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || {
  echo "ERROR: expected Ubuntu 24.04 gfortran-13 candidate $EXPECTED_PACKAGE_VERSION, got $CANDIDATE"
  exit 1
}
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "gfortran-13=$EXPECTED_PACKAGE_VERSION" curl python3-venv rsync
ACTUAL_VERSION="$(/usr/bin/gfortran-13 -dumpfullversion)"
[[ "$ACTUAL_VERSION" == "$EXPECTED_VERSION" ]] || {
  echo "ERROR: expected GNU Fortran $EXPECTED_VERSION, got $ACTUAL_VERSION"
  exit 1
}

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/fortran-runtime-pre-v100-${STAMP}.tar.gz" fortran-runtime || true
fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"
cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install "pytest>=8,<10" >/dev/null
export SC_FORTRAN_GFORTRAN_VERSION="$EXPECTED_VERSION"
export SC_FORTRAN_GFORTRAN_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION"
export SC_FORTRAN_GFORTRAN_BIN=/usr/bin/gfortran-13
export SC_FORTRAN_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_FORTRAN_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py

sudo cp deploy/sc-fortran-runtime.service /etc/systemd/system/sc-fortran-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-fortran-runtime.service >/dev/null
sudo systemctl restart sc-fortran-runtime.service
READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18099/health >/dev/null 2>&1; then READY=1; break; fi
  sleep 2
done
if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-fortran-runtime.service --no-pager || true
  sudo journalctl -u sc-fortran-runtime.service -n 160 --no-pager || true
  exit 1
fi
bash deploy/VERIFY_SC_RUNTIME_FORTRAN_V100.sh

echo "PASS - SUSTAINABLE CATALYST FORTRAN RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
