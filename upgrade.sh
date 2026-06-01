#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/diskvision/DiskVisionInspector}"
SERVICE_USER="${SERVICE_USER:-diskvision}"
SERVICE_GROUP="${SERVICE_GROUP:-diskvision}"

echo "DiskVisionInspector upgrade"
echo "Source: ${ROOT_DIR}"
echo "Target: ${INSTALL_DIR}"

if [ ! -d "${INSTALL_DIR}" ]; then
  echo "Install dir not found: ${INSTALL_DIR}" >&2
  exit 1
fi

sudo rsync -a --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "web/node_modules" \
  --exclude "__pycache__" \
  "${ROOT_DIR}/" "${INSTALL_DIR}/"
sudo chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"

sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

if command -v npm >/dev/null 2>&1; then
  sudo -u "${SERVICE_USER}" bash -lc "cd '${INSTALL_DIR}/web' && npm install && npm run build"
fi

if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl daemon-reload
  sudo systemctl restart diskvision-watchdog.service || true
  sudo systemctl restart diskvision-dashboard.service || true
fi

echo "Upgrade complete."

