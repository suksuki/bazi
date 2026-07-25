from __future__ import annotations

import argparse
import json
import os
import sys

from product.database_schema import (
    ProductDatabaseSchemaError,
    check_product_database_schema,
    inspect_product_database_schema,
    migrate_product_database_schema,
    product_schema_hash,
)


DEFAULT_LOCAL_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or explicitly migrate the DeepBazi V50 PostgreSQL schema."
    )
    parser.add_argument("action", choices=("check", "apply"))
    parser.add_argument(
        "--database-url",
        default=os.environ.get("V50_DATABASE_URL", DEFAULT_LOCAL_DATABASE_URL),
    )
    args = parser.parse_args()

    try:
        before = inspect_product_database_schema(args.database_url)
        status = (
            migrate_product_database_schema(args.database_url)
            if args.action == "apply"
            else check_product_database_schema(args.database_url)
        )
    except ProductDatabaseSchemaError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "action": args.action,
                "before": before.__dict__,
                "after": status.__dict__,
                "schema_sha256": product_schema_hash(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
