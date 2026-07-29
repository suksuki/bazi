from __future__ import annotations

import argparse
import os
from datetime import UTC, date, datetime

from abu_v60.db import engine as target_engine
from abu_v60.migration import V50OwnerImporter
from abu_v60.mingli import MingliCorpusQualificationService
from abu_v60.provenance import canonical_json
from sqlalchemy import create_engine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import and qualify one authorized V50 account corpus in V60."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--owner-profile-id", required=True)
    parser.add_argument(
        "--analysis-date",
        default=datetime.now(tz=UTC).date().isoformat(),
    )
    args = parser.parse_args()
    source_engine = create_engine(
        os.getenv(
            "V50_SOURCE_DATABASE_URL",
            "postgresql+psycopg:///qiazhi_v50?host=/tmp",
        ),
        pool_pre_ping=True,
    )
    imported = V50OwnerImporter(
        source_engine=source_engine,
        target_engine=target_engine,
    ).import_account_corpus(
        email=args.email,
        owner_profile_id=args.owner_profile_id,
    )
    result = MingliCorpusQualificationService(target_engine).qualify(
        account_ref=imported.account_ref,
        analysis_date=date.fromisoformat(args.analysis_date),
    )
    print(
        canonical_json(
            {
                "imported_profile_count": imported.profile_count,
                **result,
            }
        )
    )


if __name__ == "__main__":
    main()
