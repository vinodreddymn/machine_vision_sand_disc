from __future__ import annotations

import json

import httpx


def main() -> int:
    targets = {
        "dashboard": "http://127.0.0.1:8010/api/system/health",
        "services": "http://127.0.0.1:8010/api/system/services",
    }
    out = {}
    for name, url in targets.items():
        try:
            out[name] = httpx.get(url, timeout=2.0).json()
        except Exception as error:
            out[name] = {"status": "OFFLINE", "error": str(error)}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

