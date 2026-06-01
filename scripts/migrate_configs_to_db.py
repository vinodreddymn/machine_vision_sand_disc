#!/usr/bin/env python
"""
Migration script to load JSON configuration files into the database.
Runs on first initialization to populate the config_store table.
This is a one-time operation that creates the initial database records.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from config.settings import CONFIG_DIR, POSTGRES_DSN
from services.config_manager import ConfigurationService


def migrate_json_configs_to_db():
    """Migrate all JSON configuration files to database."""
    service = ConfigurationService(POSTGRES_DSN)
    
    config_files = {
        'tolerances': CONFIG_DIR / 'tolerances.json',
        'health_thresholds': CONFIG_DIR / 'health_thresholds.json',
        'image_retention': CONFIG_DIR / 'image_retention.json',
        'security': CONFIG_DIR / 'security.json',
        'notifications': CONFIG_DIR / 'notifications.json',
    }
    
    migration_flag = CONFIG_DIR / '.config_db_migrated'
    
    # Check if migration already completed
    if migration_flag.exists():
        print("✓ Configuration migration already completed. Skipping.")
        return
    
    print("Starting JSON configuration migration to database...")
    print(f"Database: {POSTGRES_DSN}")
    print()
    
    migrated_count = 0
    skipped_count = 0
    
    for config_key, file_path in config_files.items():
        if not file_path.exists():
            print(f"⚠ {config_key}: File not found ({file_path})")
            skipped_count += 1
            continue
        
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            # Check if config already exists in database
            existing = service.load_config(config_key)
            
            if existing:
                print(f"✓ {config_key}: Already in database (version {service.list_config_versions(config_key, limit=1)[0]['version']})")
                skipped_count += 1
            else:
                # Migrate to database
                result = service.save_config(
                    config_key,
                    config_data,
                    updated_by='migration_script',
                    description=f'Initial migration from {file_path.name}',
                    reason='Automated migration from JSON file to database'
                )
                print(f"✓ {config_key}: Migrated successfully (v{result['version']})")
                migrated_count += 1
        
        except json.JSONDecodeError as e:
            print(f"✗ {config_key}: Invalid JSON - {e}")
            skipped_count += 1
        except Exception as e:
            print(f"✗ {config_key}: Migration failed - {e}")
            skipped_count += 1
    
    print()
    print(f"Migration Summary:")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped:  {skipped_count}")
    
    # Create migration flag file
    try:
        migration_flag.write_text(f"Migrated at {datetime.now().isoformat()}")
        print()
        print("✓ Migration flag created - future runs will skip this process")
    except Exception as e:
        print(f"⚠ Could not create migration flag: {e}")
    
    print()
    print("Configuration migration completed successfully!")
    print()
    print("Next steps:")
    print("1. All configurations are now stored in PostgreSQL database")
    print("2. Use the web interface (System Configurations tab) to manage settings")
    print("3. JSON files remain on disk for reference but are no longer the source of truth")
    print("4. To reset migration, delete: " + str(migration_flag))


if __name__ == '__main__':
    try:
        migrate_json_configs_to_db()
    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
    except Exception as e:
        print(f"\nMigration failed: {e}")
        raise
