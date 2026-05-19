# Database Layout

```text
database/
  migrations/
    001_partition_inspection_records.sql
  sql/
    create_daily_partition.sql
scripts/
  manage_inspection_partitions.py
storage/
  .env
  postgres.py
  service.py
```

## Deployment Order

1. Back up `machine_vision`.
2. Run `database/migrations/001_partition_inspection_records.sql`.
3. Review and run the optional backfill section if legacy data must be copied.
4. Schedule `scripts/manage_inspection_partitions.py` once daily.
5. Update application writes so serial numbers are first reserved in `inspection_serial_registry`, then inserted into `inspection_records` in the same transaction.
