"""Image lifecycle and retention management for industrial deployments."""

from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings import OUTPUT_DIR, load_image_retention


log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetentionResult:
    deleted_files: int
    archived_files: int
    archived_bytes: int


class ImageRetentionManager:
    """Apply configurable retention policies to outputs/ and similar artifacts."""

    def __init__(self, *, now: datetime | None = None) -> None:
        self._now = now or datetime.now(timezone.utc)
        self.policy = load_image_retention()

    def enforce(self) -> RetentionResult:
        if not bool(self.policy.get("enabled", True)):
            return RetentionResult(deleted_files=0, archived_files=0, archived_bytes=0)

        deleted = 0
        archived = 0
        archived_bytes = 0

        passed_days = int(self.policy.get("passed_images_days", 30))
        failed_days = int(self.policy.get("failed_images_days", 365))
        logs_days = int(self.policy.get("logs_days", 30))

        deleted += self._delete_older_than(OUTPUT_DIR / "passed", days=passed_days)
        deleted += self._delete_older_than(OUTPUT_DIR / "failed", days=failed_days)
        deleted += self._delete_older_than(OUTPUT_DIR / "logs", days=logs_days, patterns={".log"})

        if bool(self.policy.get("archive_enabled", True)):
            archive_dir = Path(str(self.policy.get("archive_dir", "outputs/archive")))
            if not archive_dir.is_absolute():
                archive_dir = OUTPUT_DIR.parent / archive_dir
            min_age_days = int(self.policy.get("archive_min_age_days", 7))
            a_count, a_bytes = self._archive_old_files(OUTPUT_DIR, archive_dir, min_age_days=min_age_days)
            archived += a_count
            archived_bytes += a_bytes

        return RetentionResult(deleted_files=deleted, archived_files=archived, archived_bytes=archived_bytes)

    def _delete_older_than(self, directory: Path, *, days: int, patterns: set[str] | None = None) -> int:
        if not directory.exists():
            return 0
        cutoff = self._now - timedelta(days=days)
        deleted = 0
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if patterns is not None and path.suffix.lower() not in patterns:
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    path.unlink(missing_ok=True)
                    deleted += 1
            except Exception:
                continue
        if deleted:
            log.info("Retention deleted %s file(s) from %s", deleted, directory)
        return deleted

    def _archive_old_files(self, root: Path, archive_dir: Path, *, min_age_days: int) -> tuple[int, int]:
        """Move old non-critical artifacts into an archive folder (not compression yet)."""
        archive_dir.mkdir(parents=True, exist_ok=True)
        cutoff = self._now - timedelta(days=min_age_days)
        archived = 0
        archived_bytes = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.parts and "logs" in path.parts:
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    continue
                rel = path.relative_to(root)
                dest = archive_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                size = path.stat().st_size
                shutil.move(str(path), str(dest))
                archived += 1
                archived_bytes += int(size)
            except Exception:
                continue
        if archived:
            log.info("Archived %s file(s) into %s", archived, archive_dir)
        return archived, archived_bytes


def run_retention_loop(*, interval_seconds: int = 3600) -> int:
    """Run retention periodically (suitable for watchdog-managed service)."""
    while True:
        try:
            manager = ImageRetentionManager()
            result = manager.enforce()
            if result.deleted_files or result.archived_files:
                log.info(
                    "Retention summary: deleted=%s archived=%s bytes=%s",
                    result.deleted_files,
                    result.archived_files,
                    result.archived_bytes,
                )
        except Exception as error:
            log.warning("Retention loop error: %s", error)
        time.sleep(interval_seconds)

