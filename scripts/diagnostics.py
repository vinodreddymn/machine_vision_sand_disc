from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = {
        "python": sys.version,
        "platform": platform.platform(),
        "repo_root": str(root),
        "pg_dump_on_path": shutil.which("pg_dump") is not None,
        "node_on_path": shutil.which("node") is not None,
        "npm_on_path": shutil.which("npm") is not None or shutil.which("npm.cmd") is not None,
        "config_files": {
            "tolerances": str(root / "config" / "tolerances.json"),
            "health_thresholds": str(root / "config" / "health_thresholds.json"),
            "image_retention": str(root / "config" / "image_retention.json"),
            "security": str(root / "config" / "security.json"),
        },
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

