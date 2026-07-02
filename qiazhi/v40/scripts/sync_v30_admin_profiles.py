from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
V30_PACKAGE_ROOT = REPO_ROOT / "qiazhi" / "v30"
if str(V30_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(V30_PACKAGE_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v40.migration.admin_v30_profiles import sync_v30_admin_profiles_to_repository
from v40.storage import V40PostgresRepository


def default_store_path() -> Path:
    remote_snapshot = REPO_ROOT / "qiazhi" / "v30" / ".runtime" / "remote_product_sync" / "product_ui_store.13.json"
    if remote_snapshot.exists():
        return remote_snapshot
    return REPO_ROOT / "qiazhi" / "v30" / ".runtime" / "product_ui_store.json"


def build_chart_payload_from_v30_birth_input(profile: Mapping[str, Any], target_year: int) -> dict[str, Any]:
    from v30.contracts import BirthInput
    from v30.core.chart_context import build_chart_context_from_birth_input

    source_profile_id = str(profile.get("profile_id") or "v30-profile")
    birth_payload = dict(profile.get("birth_input") or {})
    birth_payload["input_id"] = source_profile_id
    birth_input = BirthInput.model_validate(birth_payload)
    result = build_chart_context_from_birth_input(
        reading_id=f"v40-sync:{source_profile_id}",
        birth_input=birth_input,
        locale="zh",
        created_at=datetime(target_year, 6, 1, 12, 0, tzinfo=timezone.utc),
    )
    if result.status != "ready" or not result.chart_context:
        return {
            "status": result.status,
            "pillars": {},
            "failures": result.failures,
        }
    time_layers = result.chart_context.time_layers if isinstance(result.chart_context.time_layers, Mapping) else {}
    luck_context = time_layers.get("luck_cycle_context") if isinstance(time_layers.get("luck_cycle_context"), Mapping) else {}
    flow_context = time_layers.get("flow_context") if isinstance(time_layers.get("flow_context"), Mapping) else {}
    return {
        "status": "ready",
        "pillars": result.four_pillar_result.pillars,
        "current_luck": str(luck_context.get("current_luck_pillar") or ""),
        "current_year": str(flow_context.get("flow_year_pillar") or ""),
        "failures": [],
    }


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
