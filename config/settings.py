"""Central project paths and tolerance loading helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DATASET_DIR = PROJECT_ROOT / "dataset"
DATASET_EXPORT_DIR = PROJECT_ROOT / "dataset_export"
LOG_DIR = OUTPUT_DIR / "logs"
STORAGE_DIR = PROJECT_ROOT / "storage"
STORAGE_ENV_FILE = STORAGE_DIR / ".env"
TOLERANCES_FILE = CONFIG_DIR / "tolerances.json"
HEALTH_THRESHOLDS_FILE = CONFIG_DIR / "health_thresholds.json"
IMAGE_RETENTION_FILE = CONFIG_DIR / "image_retention.json"
SECURITY_FILE = CONFIG_DIR / "security.json"
KIOSK_MODE = False  # Set to True to enable kiosk mode (full-screen, no cursor)

MODE_RULE_BASED = "RULE_BASED"
MODE_DATA_COLLECTION = "DATA_COLLECTION"
MODE_AI_ASSIST = "AI_ASSIST"
MODE_PRODUCTION = "PRODUCTION"
SUPPORTED_INSPECTION_MODES = {
    MODE_RULE_BASED,
    MODE_DATA_COLLECTION,
    MODE_AI_ASSIST,
    MODE_PRODUCTION,
}
INSPECTION_MODE = os.getenv("DISK_VISION_MODE", MODE_DATA_COLLECTION)
API_HOST = os.getenv("DISK_VISION_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("DISK_VISION_API_PORT", "8010"))


def _load_env_file(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE lines from one local env file."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


_storage_env = _load_env_file(STORAGE_ENV_FILE)
POSTGRES_DSN = os.getenv("DISK_VISION_POSTGRES_DSN") or (
    f"dbname={_storage_env.get('POSTGRES_DB', 'diskvision')} "
    f"user={_storage_env.get('POSTGRES_USER', 'postgres')} "
    f"password={_storage_env.get('POSTGRES_PASSWORD', '')} "
    f"host={_storage_env.get('POSTGRES_HOST', 'localhost')} "
    f"port={_storage_env.get('POSTGRES_PORT', '5432')}"
)


def load_tolerances() -> dict[str, Any]:
    """Load inspection tolerances from JSON for easy shop-floor tuning."""
    with TOLERANCES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_tolerances(tolerances: dict[str, Any]) -> None:
    """Save modified inspection tolerances back to JSON config file."""
    with TOLERANCES_FILE.open("w", encoding="utf-8") as file:
        json.dump(tolerances, file, indent=2)


def load_health_thresholds() -> dict[str, Any]:
    """Load health monitoring thresholds from JSON config."""
    with HEALTH_THRESHOLDS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_image_retention() -> dict[str, Any]:
    """Load image/log retention policy from JSON config."""
    with IMAGE_RETENTION_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_security_config() -> dict[str, Any]:
    """Load security/auth settings from JSON config."""
    with SECURITY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)
