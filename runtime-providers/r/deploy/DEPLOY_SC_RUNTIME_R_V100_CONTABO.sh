#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_R_RUNTIME_ROOT:-/opt/sustainable-catalyst/r-runtime}"

echo "=== SUSTAINABLE CATALYST R RUNTIME v1.0.0 DEPLOYMENT ==="

if ! command -v Rscript >/dev/null 2>&1; then
  echo "Rscript not found; installing Ubuntu r-base-core."
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y r-base-core
fi

Rscript --version

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst \
    -czf "/opt/sustainable-catalyst/backups/r-runtime-pre-v100-${STAMP}.tar.gz" \
    r-runtime || true
fi

sudo mkdir -p "$INSTALL_ROOT"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT"

cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install "pytest>=8,<10" >/dev/null

PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py

Rscript --vanilla -e 'x<-c(1,2,3,4,5); stopifnot(mean(x)==3); cat("PASS - native R statistics\n")'

sudo cp deploy/sc-r-runtime.service /etc/systemd/system/sc-r-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-r-runtime.service >/dev/null
sudo systemctl restart sc-r-runtime.service

READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18094/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-r-runtime.service --no-pager || true
  sudo journalctl -u sc-r-runtime.service -n 120 --no-pager || true
  exit 1
fi

bash deploy/VERIFY_SC_RUNTIME_R_V100.sh

echo "PASS - SUSTAINABLE CATALYST R RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
