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


def partition_name_for(day: date) -> str:
    """Return the canonical daily inspection partition name."""
    return f"inspection_records_{day:%Y_%m_%d}"


def ensure_partition(day: date) -> str:
    """Create one partition if missing and return its name."""
    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT public.ensure_inspection_records_partition(%s)",
                (day,),
            )
            return str(cursor.fetchone()[0])


def main() -> None:
    """Create tomorrow's partition for scheduled daily execution."""
    tomorrow = date.today() + timedelta(days=1)
    created = ensure_partition(tomorrow)
    print(f"Ensured partition exists: {created}")


if __name__ == "__main__":
    main()
