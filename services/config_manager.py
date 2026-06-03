"""Configuration management service for database-backed JSON storage with versioning and audit trail."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from config.settings import POSTGRES_DSN


class ConfigurationService:
    """Manages system configuration stored in database with version control and audit trail."""

    def __init__(self, dsn: str):
        """Initialize the configuration service."""
        self.dsn = dsn

    def _get_connection(self):
        """Get a database connection."""
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def load_config(self, config_key: str, version: int | None = None) -> dict[str, Any]:
        """Load configuration by key, optionally a specific version."""
        with self._get_connection() as conn:
            if version is None:
                # Load latest active version
                cur = conn.execute(
                    """
                    SELECT config_data FROM config_store
                    WHERE config_key = %s AND is_active = TRUE
                    ORDER BY version DESC
                    LIMIT 1
                    """,
                    (config_key,)
                )
            else:
                # Load specific version
                cur = conn.execute(
                    """
                    SELECT config_data FROM config_store
                    WHERE config_key = %s AND version = %s
                    """,
                    (config_key, version)
                )
            
            row = cur.fetchone()
            if row:
                return row["config_data"]
            return {}

    def reload_config(self, config_key: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Reload one configuration or the full catalog from the database."""
        if config_key is None:
            return self.list_all_configs()
        return self.load_config(config_key)

    def get_config_version(self, config_key: str) -> int:
        """Return the latest stored version for one configuration."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS latest_version FROM config_store WHERE config_key = %s",
                (config_key,),
            )
            row = cur.fetchone()
            return int(row["latest_version"] or 0) if row else 0

    def save_config(
        self,
        config_key: str,
        config_data: dict[str, Any],
        updated_by: str = "system",
        description: str | None = None,
        reason: str | None = None,
        ip_address: str | None = None
    ) -> dict[str, Any]:
        """Save configuration with automatic versioning and audit trail."""
        with self._get_connection() as conn:
            # Get current version
            cur = conn.execute(
                "SELECT MAX(version) as max_version FROM config_store WHERE config_key = %s",
                (config_key,)
            )
            row = cur.fetchone()
            current_version = (row["max_version"] or 0) if row else 0
            new_version = current_version + 1

            # Get old value for audit
            old_value = self.load_config(config_key) if current_version > 0 else None

            # Insert new config version
            cur = conn.execute(
                """
                INSERT INTO config_store
                (config_key, config_type, config_data, version, updated_by, description, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, config_key, version, created_at, updated_at
                """,
                (config_key, "json", Jsonb(config_data), new_version, updated_by, description, True)
            )
            result = cur.fetchone()

            # Deactivate previous versions
            conn.execute(
                "UPDATE config_store SET is_active = FALSE WHERE config_key = %s AND version < %s",
                (config_key, new_version)
            )

            # Audit log entry
            conn.execute(
                """
                INSERT INTO config_audit_log
                (config_key, action, old_value, new_value, version_number, changed_by, reason, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (config_key, "UPDATE", Jsonb(old_value) if old_value else None, Jsonb(config_data), 
                 new_version, updated_by, reason, ip_address)
            )

            conn.commit()

            return {
                "id": result["id"],
                "config_key": result["config_key"],
                "version": result["version"],
                "created_at": result["created_at"],
                "updated_at": result["updated_at"]
            }

    def list_config_versions(self, config_key: str, limit: int = 10) -> list[dict[str, Any]]:
        """List all versions of a configuration."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, config_key, version, created_at, updated_at, updated_by, description, is_active
                FROM config_store
                WHERE config_key = %s
                ORDER BY version DESC
                LIMIT %s
                """,
                (config_key, limit)
            )
            return [dict(row) for row in cur.fetchall()]

    def rollback_config(
        self,
        config_key: str,
        version: int,
        rolled_back_by: str = "system",
        reason: str | None = None
    ) -> dict[str, Any]:
        """Rollback configuration to a previous version."""
        with self._get_connection() as conn:
            # Get the target version data
            cur = conn.execute(
                "SELECT config_data FROM config_store WHERE config_key = %s AND version = %s",
                (config_key, version)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Version {version} not found for {config_key}")

            config_data = row["config_data"]

            # Save as new version (which triggers audit)
            return self.save_config(
                config_key,
                config_data,
                updated_by=rolled_back_by,
                description=f"Rollback to version {version}",
                reason=reason or f"Rolled back from version {version}"
            )

    def get_audit_log(
        self,
        config_key: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get audit log for configuration changes."""
        with self._get_connection() as conn:
            if config_key:
                cur = conn.execute(
                    """
                    SELECT * FROM config_audit_log
                    WHERE config_key = %s
                    ORDER BY changed_at DESC
                    LIMIT %s
                    """,
                    (config_key, limit)
                )
            else:
                cur = conn.execute(
                    """
                    SELECT * FROM config_audit_log
                    ORDER BY changed_at DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
            return [dict(row) for row in cur.fetchall()]

    def list_all_configs(self) -> list[dict[str, Any]]:
        """List all active configurations."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT DISTINCT config_key FROM config_store
                WHERE is_active = TRUE
                ORDER BY config_key
                """
            )
            configs = []
            for row in cur.fetchall():
                config_key = row["config_key"]
                config_data = self.load_config(config_key)
                configs.append({
                    "config_key": config_key,
                    "data": config_data,
                    "versions": self.list_config_versions(config_key, limit=3)
                })
            return configs

    def sync_file_to_db(self, config_key: str, file_path: Path, updated_by: str = "system") -> dict[str, Any]:
        """Sync a JSON file to the database."""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        return self.save_config(
            config_key,
            config_data,
            updated_by=updated_by,
            description=f"Synced from {file_path.name}",
            reason="File synchronization"
        )

    def sync_db_to_file(self, config_key: str, file_path: Path) -> None:
        """Sync a configuration from database to JSON file."""
        config_data = self.load_config(config_key)
        if not config_data:
            raise ValueError(f"No configuration found for key: {config_key}")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2)


def get_config_service() -> ConfigurationService:
    """Factory function to create a ConfigurationService instance."""
    return ConfigurationService(POSTGRES_DSN)
