from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v30.config import _validate_database_url
from v30.storage.postgres_schema import CREATE_TABLE_STATEMENTS


def main() -> int:
    database_url = os.getenv("V30_DATABASE_URL")
    if not database_url:
        print("blocked_missing_V30_DATABASE_URL", file=sys.stderr)
        return 2
    _validate_database_url(database_url)
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for sql in CREATE_TABLE_STATEMENTS.values():
                cursor.execute(sql)
        connection.commit()
    print("v30.postgres.schema: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
