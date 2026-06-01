# JSON Configuration Migration to Database

## Overview

This document describes the migration of JSON configuration files to a PostgreSQL database with full version control, audit trails, and Industry 4.0 compliance features.

## What Changed

### Before
- Configuration files stored as JSON on disk
- Limited version control
- No audit trail for configuration changes
- No centralized change tracking

### After
- All configurations stored in PostgreSQL database
- Automatic versioning with rollback capability
- Complete audit trail with change tracking
- User attribution for all changes
- Change reason documentation
- IP address logging (for remote changes)

## Configuration Files Migrated

The following JSON configuration files have been migrated to the database:

1. **tolerances.json** - Inspection tolerance settings
2. **health_thresholds.json** - System health monitoring thresholds
3. **image_retention.json** - Image storage retention policies
4. **security.json** - Security configuration
5. **notifications.json** - Notification system settings

## Database Schema

### config_store table
Stores all configuration versions with metadata.

```sql
CREATE TABLE config_store (
    id BIGSERIAL PRIMARY KEY,
    config_key TEXT NOT NULL,
    config_type TEXT NOT NULL DEFAULT 'json',
    config_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by TEXT,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(config_key, version)
);
```

### config_audit_log table
Records all configuration changes for compliance and traceability.

```sql
CREATE TABLE config_audit_log (
    id BIGSERIAL PRIMARY KEY,
    config_key TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    version_number INTEGER,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT,
    ip_address TEXT
);
```

## API Endpoints

### Get All Configurations
```
GET /api/config/all
```
Returns all active configurations with metadata.

### Get Specific Configuration
```
GET /api/config/{config_key}
```
Returns the current version of a specific configuration.

### Save Configuration
```
POST /api/config/{config_key}
```
Saves a configuration with automatic versioning.

Parameters:
- `config_data`: The configuration object (JSON)
- `description`: Optional description of changes
- `reason`: Optional reason for audit trail

Response:
```json
{
  "id": 1,
  "config_key": "tolerances",
  "version": 2,
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T10:00:00Z"
}
```

### Get Configuration Versions
```
GET /api/config/{config_key}/versions?limit=10
```
Returns version history for a configuration.

### Rollback Configuration
```
POST /api/config/{config_key}/rollback/{version}
```
Reverts to a previous version.

### Get Audit Log
```
GET /api/config/audit-log?config_key=tolerances&limit=100
```
Returns audit trail for configuration changes.

## Web GUI Features

### Configuration Manager
Located in Settings → System Configurations tab

**Tabs:**
1. **Overview** - View current configuration with metadata
2. **Edit Configuration** - JSON editor with syntax validation
3. **Version History** - View all versions with rollback capability
4. **Audit Log** - Complete change history with traceability

**Features:**
- Live JSON syntax validation
- JSON formatting and minification tools
- Version comparison
- One-click rollback to previous versions
- Change documentation (description and reason)
- Full audit trail visibility

### Admin Page Enhancements

**Compliance Tab:**
- System compliance status overview
- Industry 4.0 compliance verification
- Data traceability confirmation
- User access control status

**Configuration Audit Tab:**
- All configuration changes in chronological order
- User attribution for each change
- Change reasons and descriptions
- Version tracking
- Searchable audit trail

## Industry 4.0 Compliance Features

1. **Data Traceability**
   - Every configuration change is logged
   - User attribution required
   - Timestamp for all changes
   - Change reason documentation

2. **Version Control**
   - Automatic versioning
   - Full rollback capability
   - Version comparison
   - Historical record retention

3. **User Access Control**
   - Role-based access (OPERATOR, SUPERVISOR, ADMIN)
   - Admin-only configuration changes
   - User authentication required
   - Activity audit logging

4. **Change Tracking**
   - Complete audit trail
   - User, date, and reason for all changes
   - Change validation
   - Immutable log storage

5. **Security**
   - Database-backed storage
   - Access control via role-based permissions
   - API token authentication
   - Change authorization tracking

## Migration Instructions

### 1. Run Database Migrations
```bash
cd database/migrations
# Run migrations using your preferred tool
# (e.g., psql, Alembic, etc.)
```

### 2. Run Configuration Migration Script
```bash
python scripts/migrate_configs_to_db.py
```

This script will:
- Read all JSON configuration files
- Check if configurations already exist in database
- Migrate any missing configurations
- Create a migration flag file to prevent re-running

### 3. Verify Migration
```bash
curl -X GET http://localhost:8010/api/config/all
```

Should return:
```json
[
  {
    "config_key": "tolerances",
    "data": { ... },
    "versions": [ ... ]
  },
  ...
]
```

## Using the Configuration Manager

### View Configuration
1. Navigate to Settings → System Configurations
2. Select configuration from left sidebar
3. View current settings in Overview tab

### Edit Configuration
1. Click "Edit Configuration" tab
2. Modify JSON in the editor
3. Provide a description of changes (optional)
4. Provide change reason for audit trail (recommended)
5. Click "Save Configuration"

### Rollback Configuration
1. Go to "Version History" tab
2. Find the version to restore
3. Click "Rollback to vX"
4. Confirm the action

### View Change History
1. Go to "Audit Log" tab
2. See all changes with timestamps, users, and reasons
3. Filter by configuration type (if needed)

## Troubleshooting

### Migration Flag Exists
If migration keeps getting skipped, delete the flag file:
```bash
rm config/.config_db_migrated
```

### Configuration Not Showing
1. Verify migration was successful:
   ```bash
   python scripts/migrate_configs_to_db.py
   ```
2. Check database connection:
   ```bash
   curl -X GET http://localhost:8010/api/config/all
   ```

### Unable to Save Configuration
- Check user role (ADMIN required)
- Verify authentication token
- Check JSON syntax validity

## Best Practices

1. **Always provide change reasons** - Important for compliance and troubleshooting
2. **Review changes before saving** - Use the JSON editor's format feature
3. **Document significant changes** - Use description field
4. **Backup before major changes** - Use Admin → Backups
5. **Monitor audit logs** - Regularly review for unauthorized changes

## Rollback Policy

Configuration changes can be rolled back at any time to any previous version:

1. **Recent changes**: Can be rolled back immediately
2. **Historical versions**: Kept indefinitely (configurable)
3. **Audit trail**: All rollbacks are logged

## Support

For issues or questions:
1. Check audit logs for recent changes
2. Review configuration JSON syntax
3. Verify user permissions
4. Check API endpoint responses

## API Examples

### Save Configuration with Reason
```bash
curl -X POST http://localhost:8010/api/config/tolerances \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "expected_hole_count": 5,
    "outer_radius_px": { "min": 80, "max": 450 },
    "hole_diameter_px": { "min": 12, "max": 70 },
    "description": "Adjusted hole diameter tolerance",
    "reason": "Product specification updated per engineering"
  }'
```

### Get Configuration Versions
```bash
curl -X GET "http://localhost:8010/api/config/tolerances/versions?limit=5"
```

### Rollback Configuration
```bash
curl -X POST http://localhost:8010/api/config/tolerances/rollback/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"reason": "Reverting invalid changes"}'
```

### View Audit Trail
```bash
curl -X GET "http://localhost:8010/api/config/audit-log?config_key=tolerances&limit=20"
```
