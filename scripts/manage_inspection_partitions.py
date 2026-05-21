"""Create tomorrow's inspection_records partition safely and idempotently."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import POSTGRES_DSN


def partition_names_for(day: date) -> tuple[str, str]:
    """Return the canonical daily inspection partition names for both stages."""
    return f"stage1_inspection_records_{day:%Y_%m_%d}", f"stage2_inspection_records_{day:%Y_%m_%d}"


def ensure_partitions(day: date) -> tuple[str, str]:
    """Create partitions for both stages if missing and return their names."""
    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT public.ensure_stage1_partition(%s)",
                (day,),
            )
            p1 = str(cursor.fetchone()[0])
            cursor.execute(
                "SELECT public.ensure_stage2_partition(%s)",
                (day,),
            )
            p2 = str(cursor.fetchone()[0])
            return p1, p2


def main() -> None:
    """Create tomorrow's partitions for scheduled daily execution."""
    tomorrow = date.today() + timedelta(days=1)
    p1, p2 = ensure_partitions(tomorrow)
    print(f"Ensured Stage 1 partition exists: {p1}")
    print(f"Ensured Stage 2 partition exists: {p2}")


if __name__ == "__main__":
    main()

