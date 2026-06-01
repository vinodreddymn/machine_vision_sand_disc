from __future__ import annotations

import json
from pathlib import Path

import httpx


def main() -> int:
    url = "http://127.0.0.1:8115/backup/create"
    res = httpx.post(url, timeout=600.0)
    res.raise_for_status()
    payload = res.json()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

