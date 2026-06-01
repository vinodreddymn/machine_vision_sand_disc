#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/diskvision/DiskVisionInspector}"
SERVICE_USER="${SERVICE_USER:-diskvision}"
SERVICE_GROUP="${SERVICE_GROUP:-diskvision}"

echo "DiskVisionInspector installer"
echo "Source: ${ROOT_DIR}"
echo "Target: ${INSTALL_DIR}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

require_cmd python3
require_cmd rsync

if command -v systemctl >/dev/null 2>&1; then
  HAS_SYSTEMD=1
else
  HAS_SYSTEMD=0
fi

echo "Ensuring service user/group..."
if ! getent group "${SERVICE_GROUP}" >/dev/null 2>&1; then
  sudo groupadd --system "${SERVICE_GROUP}"
fi
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin --gid "${SERVICE_GROUP}" "${SERVICE_USER}"
fi

echo "Syncing project files..."
sudo mkdir -p "${INSTALL_DIR}"
sudo rsync -a --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "web/node_modules" \
  --exclude "__pycache__" \
  "${ROOT_DIR}/" "${INSTALL_DIR}/"
sudo chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"

echo "Creating venv + installing Python deps..."
sudo -u "${SERVICE_USER}" python3 -m venv "${INSTALL_DIR}/.venv"
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

if command -v npm >/dev/null 2>&1; then
  echo "Building web dashboard..."
  sudo -u "${SERVICE_USER}" bash -lc "cd '${INSTALL_DIR}/web' && npm install && npm run build"
else
  echo "npm not found; skipping web build (install node/npm to build web dashboard)."
fi

echo "Preparing env file..."
sudo mkdir -p "${INSTALL_DIR}/deploy/env"
if [ ! -f "${INSTALL_DIR}/deploy/env/diskvision.env" ]; then
  sudo cp "${INSTALL_DIR}/deploy/env/diskvision.env.example" "${INSTALL_DIR}/deploy/env/diskvision.env"
  sudo chown "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}/deploy/env/diskvision.env"
  echo "Created ${INSTALL_DIR}/deploy/env/diskvision.env"
fi

if [ "${HAS_SYSTEMD}" -eq 1 ]; then
  echo "Installing systemd units..."
  sudo cp "${INSTALL_DIR}/deploy/systemd/diskvision-watchdog.service" /etc/systemd/system/diskvision-watchdog.service
  sudo cp "${INSTALL_DIR}/deploy/systemd/diskvision-dashboard.service" /etc/systemd/system/diskvision-dashboard.service
  sudo systemctl daemon-reload
  sudo systemctl enable diskvision-watchdog.service
  sudo systemctl restart diskvision-watchdog.service
  echo "systemd: diskvision-watchdog started."
else
  echo "systemd not found; install complete without service registration."
  echo "Manual run: ${INSTALL_DIR}/.venv/bin/python -m disk_vision_inspector.run watchdog"
fi

echo "Install complete."

