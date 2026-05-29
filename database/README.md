# Database Layout

```text
database/
  migrations/
    001_partition_inspection_records.sql
    002_split_stage_tables.sql
    003_single_station_schema.sql
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

1. Back up the PostgreSQL database.
2. Run `database/migrations/003_single_station_schema.sql`.
3. Review and run the optional Stage 1 backfill section only if existing top-side records should become single-station history.
4. Schedule `scripts/manage_inspection_partitions.py` once daily.
5. Application writes now reserve serial numbers in `inspection_serial_registry`, then insert into `inspection_records` in the same transaction.
