# Troubleshooting Guide (Baseline)

Scripts:
- `python scripts/diagnostics.py`
- `python scripts/health_check.py`
- `scripts/health-check.sh` (Linux)

Common issues:
- Port already in use: run one instance at a time or change ports via env.
- DB offline: system continues but history/alarms persistence degrades to memory.

