from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from config.settings import CONFIG_DIR, OUTPUT_DIR, POSTGRES_DSN
from disk_vision_inspector.shared.logging import configure_service_logging


log = logging.getLogger(__name__)


def _run_pg_dump(dest: Path) -> bool:
    try:
        result = subprocess.run(
            ["pg_dump", POSTGRES_DSN, "-f", str(dest)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            log.warning("pg_dump failed: %s", result.stderr.strip())
            return False
        return True
    except FileNotFoundError:
        log.warning("pg_dump not found on PATH; skipping DB dump.")
        return False


def _zip_dir(src: Path, dest_zip: Path) -> None:
    import zipfile

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in src.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(src)))


def run_backup_service() -> int:
    configure_service_logging(service_name="backup_service")
    app = FastAPI(title="DiskVisionInspector Backup Service")

    backup_root = Path(os.getenv("DISK_VISION_BACKUP_DIR", str(OUTPUT_DIR / "backups")))

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"name": "backup_service", "status": "ONLINE", "timestamp": time.time()}

    @app.post("/backup/create")
    def create_backup() -> dict[str, Any]:
        ts = time.strftime("%Y%m%d_%H%M%S")
        bundle_dir = backup_root / f"bundle_{ts}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Config snapshot
        cfg_zip = bundle_dir / "config.zip"
        _zip_dir(CONFIG_DIR, cfg_zip)

        # Outputs snapshot (best-effort; can be large)
        outputs_zip = bundle_dir / "outputs.zip"
        _zip_dir(OUTPUT_DIR, outputs_zip)

        # DB dump (optional)
        db_dump = bundle_dir / "database.sql"
        dumped = _run_pg_dump(db_dump)
        if not dumped and db_dump.exists():
            db_dump.unlink(missing_ok=True)

        return {
            "status": "success",
            "bundle_dir": str(bundle_dir),
            "config_zip": str(cfg_zip),
            "outputs_zip": str(outputs_zip),
            "database_dump": str(db_dump) if dumped else None,
        }

    @app.post("/backup/restore")
    def restore_backup(bundle_dir: str) -> dict[str, Any]:
        # This is a scaffold: full restore wizard comes later.
        bundle = Path(bundle_dir)
        if not bundle.exists():
            raise HTTPException(status_code=404, detail="Bundle not found")
        return {"status": "not_implemented", "bundle_dir": str(bundle)}

    import uvicorn

    port = int(os.getenv("DISK_VISION_BACKUP_PORT", "8115"))
    log.info("Backup service listening on 127.0.0.1:%s", port)
    uvicorn.run(app, host="127.0.0.1", port=port)
    return 0

