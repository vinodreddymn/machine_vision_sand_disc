# AI Data Cleanup System - User Guide

## Overview

The AI Data Cleanup System provides tools to safely delete old training data, inspection outputs, and optionally inspection records from the database. This allows you to start fresh training on new parts without carrying over old data that may bias the AI models.

## Components Created

### 1. Backend Script: `scripts/cleanup_ai_data.py`

A command-line utility for manual cleanup operations.

**Usage:**

```bash
# Delete training dataset only (default)
python scripts/cleanup_ai_data.py --dataset-only

# Delete inspection output files
python scripts/cleanup_ai_data.py --outputs-only

# Delete both dataset and outputs
python scripts/cleanup_ai_data.py

# Delete everything including database records
python scripts/cleanup_ai_data.py --full

# Delete dataset and outputs but keep database
python scripts/cleanup_ai_data.py --full --keep-database

# Skip confirmation prompts (for automation)
python scripts/cleanup_ai_data.py --full --confirm
```

**Features:**

- ✅ Safely counts items before deletion
- ✅ Preserves empty directory structure for future use
- ✅ Generates timestamped cleanup reports
- ✅ Reports total storage freed
- ✅ Prevents accidental data loss with confirmation prompts
- ✅ Supports both interactive and automated modes

**Output Report:**

```
============================================================
AI DATA CLEANUP REPORT
Timestamp: 2026-06-01T12:34:56.789012
============================================================

📦 TRAINING DATASET CLEANUP:
  • Good images deleted: 150
  • Defect images deleted: 45
  • Metadata files deleted: 195
  • Storage freed: 2.45 MB

📂 INSPECTION OUTPUT CLEANUP:
  • Passed images deleted: 320
  • Failed images deleted: 28
  • Log files deleted: 348
  • Storage freed: 5.67 MB

🗄️  DATABASE CLEANUP:
  • Inspection records deleted: 500
  • Status: SUCCESS
  • Message: Deleted 500 inspection records from database

============================================================
TOTAL STORAGE FREED: 8.12 MB
============================================================

✅ System ready for new training data collection
```

### 2. Backend API Endpoints

#### GET `/api/admin/cleanup/status`

Get current size and count of AI training data.

**Authentication:** ADMIN role required

**Response:**

```json
{
  "training_data": {
    "good_images": 150,
    "defect_images": 45,
    "total_images": 195,
    "size_mb": 2.45
  },
  "inspection_outputs": {
    "passed_images": 320,
    "failed_images": 28,
    "total_images": 348,
    "size_mb": 5.67
  },
  "database": {
    "inspection_records": 500
  }
}
```

#### POST `/api/admin/cleanup/execute`

Execute cleanup of specified data types.

**Authentication:** ADMIN role required

**Request Body:**

```json
{
  "clean_dataset": true,
  "clean_outputs": false,
  "clean_database": false
}
```

**Response:**

```json
{
  "status": "success",
  "output": "✓ Deleted: /path/to/dataset/good...",
  "return_code": 0
}
```

### 3. Web GUI Component: Cleanup Manager

**Location:** Admin Page → Data Management Tab

**Features:**

- 📊 **Data Status Cards** - Shows current dataset size and counts
  - Training Dataset (good/defect images)
  - Inspection Outputs (passed/failed images)
  - Database Records (inspection history)

- ☑️ **Cleanup Options** - Checkboxes to select what to delete
  - Training Dataset
  - Inspection Outputs
  - Inspection History (database)

- 💾 **Storage Estimator** - Shows total storage to be freed

- ⚠️ **Confirmation Dialog** - Two-stage confirmation to prevent accidents

- 📄 **Execution Report** - Shows detailed output of cleanup operation

### 4. Frontend Service: `services/cleanupService.ts`

TypeScript service for communicating with cleanup endpoints.

**Key Functions:**

```typescript
// Get status of all AI data
const status = await getCleanupStatus();

// Execute cleanup with options
const result = await executeCleanup({
  cleanDataset: true,
  cleanOutputs: false,
  cleanDatabase: false
});

// Format bytes to human-readable size
const sizeStr = formatSize(2.45); // Returns "2.45 MB"
```

## Usage Workflow

### Via Web GUI (Recommended for users)

1. Navigate to **Admin** page
2. Click **Data Management** tab
3. Review current data sizes in status cards
4. Check boxes for items to delete
5. Click **Delete Selected Data**
6. Review confirmation dialog
7. Click **Yes, Delete All** to confirm
8. Monitor cleanup progress and review results

### Via Command Line (Recommended for automation)

```bash
# List what would be deleted
python scripts/cleanup_ai_data.py

# Delete only training data
python scripts/cleanup_ai_data.py --dataset-only --confirm

# Full cleanup for starting fresh
python scripts/cleanup_ai_data.py --full --confirm
```

### Via API (For system integration)

```bash
# Check status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8010/api/admin/cleanup/status

# Execute cleanup
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"clean_dataset": true, "clean_outputs": false, "clean_database": false}' \
  http://localhost:8010/api/admin/cleanup/execute
```

## Data Deletion Details

### Training Dataset Cleanup

**Deletes:**
- `dataset/good/station1/*` - Good part images
- `dataset/good/station2/*` - Good part images (station 2)
- `dataset/defect/station1/*` - Defective part images
- `dataset/defect/station2/*` - Defective part images (station 2)
- `dataset/metadata/*.json` - Label metadata files

**Preserves:**
- Empty directory structure for future data collection
- All other configuration files

### Inspection Outputs Cleanup

**Deletes:**
- `outputs/passed/*` - Passed inspection images
- `outputs/failed/*` - Failed inspection images
- `outputs/logs/*` - Log files

**Preserves:**
- `outputs/` directory structure
- Latest cleanup reports

### Database Cleanup

**Deletes:**
- All rows from `inspection_records` table
- ⚠️ **CANNOT BE UNDONE** - No backup is automatically created

**Operation:**
- Executed directly on PostgreSQL
- Use `--keep-database` flag to avoid this
- Consider backing up database first if needed

## Safety Features

✅ **Two-Stage Confirmation**
- First click just shows confirmation dialog
- Second click actually deletes data

✅ **Size Estimation**
- Shows exactly how much storage will be freed
- Breaks down by category

✅ **Timestamp Reporting**
- All cleanup reports saved with timestamp
- Easy to track when cleanups were performed
- Reports saved to: `outputs/cleanup_report_YYYYMMDD_HHMMSS.txt`

✅ **Role-Based Access**
- Only ADMIN users can perform cleanup
- Prevents accidental deletion by operators

✅ **Dry-Run Support**
- Backend script shows what would be deleted
- Run without `--confirm` flag to preview only

## Cleanup Reports

Cleanup reports are automatically saved to:

```
outputs/cleanup_report_20260601_123456.txt
```

Each report includes:
- Timestamp of operation
- Number of files deleted
- Storage freed
- Detailed breakdown by category
- Database operation results
- Final confirmation message

## Best Practices

### Before Cleanup

1. **Verify database backup** (if deleting database)
   ```bash
   # Take PostgreSQL backup
   pg_dump diskvision > backup_20260601.sql
   ```

2. **Stop the application**
   ```bash
   # Stop main.py
   ```

3. **Review current data size**
   - Use GUI to check status
   - Confirm you want to delete shown data

### After Cleanup

1. **Verify cleanup completed**
   - Check cleanup report in `outputs/` folder
   - Verify successful status message

2. **Restart application**
   ```bash
   python main.py --web
   ```

3. **Start new data collection**
   - Switch to DATA_COLLECTION mode
   - Begin training on new parts

### For Database Recovery

If you accidentally deleted database records, you have options:

1. **If backup exists:**
   ```bash
   psql diskvision < backup_20260601.sql
   ```

2. **If no backup:**
   - Records are permanently deleted
   - This is why confirmation is required

## Troubleshooting

### Issue: "Storage is offline" error

**Solution:** Ensure PostgreSQL is running before cleanup
```bash
# Check if PostgreSQL is running
Get-Process postgres

# Or verify connection string is correct
```

### Issue: Permission denied when deleting files

**Solution:** Ensure application has write permissions to dataset directories
```bash
# Check permissions
Get-Acl c:\path\to\dataset\

# Grant permissions if needed
```

### Issue: Cleanup hangs or times out

**Solution:** Try cleanup via CLI instead of GUI
```bash
python scripts/cleanup_ai_data.py --dataset-only --confirm
```

## Schedule Cleanup

For regular maintenance, consider scheduling cleanup:

### Windows Task Scheduler

```powershell
# Create scheduled task for weekly cleanup
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2AM
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts/cleanup_ai_data.py --confirm"
Register-ScheduledTask -TaskName "DiskVision Cleanup" -Trigger $trigger -Action $action
```

### Python Schedule

```python
import schedule
import subprocess
import time

def cleanup():
    subprocess.run([
        "python",
        "scripts/cleanup_ai_data.py",
        "--full",
        "--confirm"
    ])

schedule.every().sunday.at("02:00").do(cleanup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Summary

The cleanup system provides safe, auditable data removal for starting fresh AI training cycles. Use it when:

- ✅ Starting training on new part types
- ✅ Archiving old inspection data
- ✅ Reclaiming storage space
- ✅ Resetting system for production use

Always verify data before deletion, especially database records which cannot be recovered without a backup.
