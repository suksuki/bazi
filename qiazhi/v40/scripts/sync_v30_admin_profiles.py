from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
V30_PACKAGE_ROOT = REPO_ROOT / "qiazhi" / "v30"
if str(V30_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(V30_PACKAGE_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v40.migration.admin_v30_profiles import (
    build_chart_payload_from_v30_birth_input,
    default_v30_product_store_path,
    sync_v30_admin_profiles_to_repository,
)
from v40.storage import V40PostgresRepository


def default_store_path() -> Path:
    return default_v30_product_store_path()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the single V30 admin account and its Bazi profiles into V40.")
    parser.add_argument("--source-store", type=Path, default=default_store_path())
    args = parser.parse_args()

    repository = V40PostgresRepository.from_env()
    result = sync_v30_admin_profiles_to_repository(
        repository=repository,
        source_store_path=args.source_store,
        chart_builder=build_chart_payload_from_v30_birth_input,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.skipped_profile_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
