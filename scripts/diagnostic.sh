#!/usr/bin/env bash
set -euo pipefail

python3 scripts/diagnostics.py
python3 scripts/health_check.py || true

