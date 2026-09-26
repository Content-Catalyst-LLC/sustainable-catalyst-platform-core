#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_STAN_RUNTIME_ROOT:-/opt/sustainable-catalyst/stan-runtime}"
DATA_ROOT="${SC_STAN_DATA_ROOT:-/var/lib/sc-stan-runtime}"
CMDSTAN_VERSION="${SC_STAN_CMDSTAN_VERSION:-2.36.0}"

echo "=== SUSTAINABLE CATALYST STAN RUNTIME v1.0.0 DEPLOYMENT ==="

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential \
  git \
  curl \
  python3-venv

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst \
    -czf "/opt/sustainable-catalyst/backups/stan-runtime-pre-v100-${STAMP}.tar.gz" \
    stan-runtime || true
fi

sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/models"
sudo rsync -a --delete \
  --exclude '.venv' \
  --exclude '.cmdstan' \
  "$SRC/" "$INSTALL_ROOT/"

sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"

cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install "pytest>=8,<10" >/dev/null

export SC_STAN_CMDSTAN_VERSION="$CMDSTAN_VERSION"
export SC_STAN_CMDSTAN_ROOT="$INSTALL_ROOT/.cmdstan"
export SC_STAN_CMDSTAN_HOME="$INSTALL_ROOT/.cmdstan/cmdstan-$CMDSTAN_VERSION"
export SC_STAN_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_STAN_MODEL_ROOT="$DATA_ROOT/models"

PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py install_cmdstan.py

echo "=== INSTALL / VERIFY PINNED CMDSTAN ==="
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python install_cmdstan.py

"$SC_STAN_CMDSTAN_HOME/bin/stanc" --version

sudo cp deploy/sc-stan-runtime.service /etc/systemd/system/sc-stan-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-stan-runtime.service >/dev/null
sudo systemctl restart sc-stan-runtime.service

READY=0
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:18095/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-stan-runtime.service --no-pager || true
  sudo journalctl -u sc-stan-runtime.service -n 160 --no-pager || true
  exit 1
fi

bash deploy/VERIFY_SC_RUNTIME_STAN_V100.sh

echo "PASS - SUSTAINABLE CATALYST STAN RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
