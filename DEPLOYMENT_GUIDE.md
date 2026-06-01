# Deployment Guide (Baseline)

## Linux (systemd)

Scripts:
- `install.sh`
- `upgrade.sh`

Units:
- `deploy/systemd/diskvision-watchdog.service`
- `deploy/systemd/diskvision-dashboard.service`

Environment file:
- `deploy/env/diskvision.env` (copy from `.example`)

