from __future__ import annotations

import argparse
import os
from dataclasses import asdict

from abu_v60.db import engine as target_engine
from abu_v60.migration import V50OwnerImporter
from abu_v60.provenance import canonical_json
from sqlalchemy import create_engine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Whitelist-import one V50 account and birth input into V60."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--profile-id", required=True)
    args = parser.parse_args()

    source_url = os.getenv(
        "V50_SOURCE_DATABASE_URL",
        "postgresql+psycopg:///qiazhi_v50?host=/tmp",
    )
    source_engine = create_engine(source_url, pool_pre_ping=True)
    importer = V50OwnerImporter(source_engine=source_engine, target_engine=target_engine)
    result = importer.import_selected_profile(email=args.email, profile_id=args.profile_id)
    print(canonical_json(asdict(result)))


if __name__ == "__main__":
    main()
