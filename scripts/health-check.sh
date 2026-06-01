#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8010}"

curl -fsS "http://${HOST}:${PORT}/api/system/health" | python3 -m json.tool >/dev/null
curl -fsS "http://${HOST}:${PORT}/api/system/devices" | python3 -m json.tool >/dev/null
curl -fsS "http://${HOST}:${PORT}/api/system/services" | python3 -m json.tool >/dev/null
echo "OK"

