from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v40.auth.accounts import BUILTIN_ADMIN_USER_ID, build_builtin_admin_account
from v40.contracts.chart import BaziChartFacts, BirthInputCanonical, ZiweiChartFacts
from v40.contracts.user import BaziProfileRecord, UserAccountInternal
from v40.storage.postgres import V40PostgresRepository


ADMIN_V30_ACTOR_IDS = frozenset({"v20-admin", "admin"})
ADMIN_V30_OWNER_NAMES = frozenset({"admin"})
DEFAULT_TARGET_YEAR = 2026

ChartBuildPayload = dict[str, Any]
ChartBuilder = Callable[[Mapping[str, Any], int], ChartBuildPayload]


@dataclass(frozen=True)
class AdminProfileSyncResult:
    version: str
    admin_user: dict[str, object]
    source_store: str
    source_profile_count: int
    synced_profile_count: int
    skipped_profile_count: int
    synced_profiles: list[dict[str, object]]
    skipped_profiles: list[dict[str, object]]
    boundary: str = "v40_admin_profile_sync_imports_v30_admin_profiles_without_mutating_v30"


def load_v30_product_store(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def default_v30_product_store_path() -> Path:
    qiazhi_root = Path(__file__).resolve().parents[3]
    remote_snapshot = qiazhi_root / "v30" / ".runtime" / "remote_product_sync" / "product_ui_store.13.json"
    if remote_snapshot.exists():
        return remote_snapshot
    return qiazhi_root / "v30" / ".runtime" / "product_ui_store.json"


def build_chart_payload_from_v30_birth_input(profile: Mapping[str, Any], target_year: int) -> dict[str, Any]:
    qiazhi_root = Path(__file__).resolve().parents[3]
    v30_package_root = qiazhi_root / "v30"
    if str(v30_package_root) not in sys.path:
        sys.path.insert(0, str(v30_package_root))

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


def select_v30_admin_profiles(store: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_profiles = store.get("profiles", {})
    if not isinstance(raw_profiles, Mapping):
        return []
    selected = []
    for key, raw_profile in raw_profiles.items():
        if not isinstance(raw_profile, Mapping):
            continue
        actor_id = str(raw_profile.get("actor_id") or "").strip()
        owner_username = str(raw_profile.get("owner_username") or "").strip().lower()
        if actor_id in ADMIN_V30_ACTOR_IDS or owner_username in ADMIN_V30_OWNER_NAMES:
            profile = dict(raw_profile)
            profile.setdefault("profile_id", str(key))
            selected.append(profile)
    selected.sort(key=lambda item: (str(item.get("display_name") or ""), str(item.get("profile_id") or "")))
    return selected


def build_admin_account() -> UserAccountInternal:
    return build_builtin_admin_account()


def convert_v30_profile_to_v40(
    profile: Mapping[str, Any],
    *,
    user_id: str = BUILTIN_ADMIN_USER_ID,
    target_year: int | None = None,
    chart_builder: ChartBuilder | None = None,
    is_default: bool = False,
) -> BaziProfileRecord:
    source_profile_id = str(profile.get("profile_id") or "").strip()
    if not source_profile_id:
        raise ValueError("V30 profile requires profile_id")
    birth_payload = profile.get("birth_input")
    if not isinstance(birth_payload, Mapping):
        raise ValueError(f"V30 profile {source_profile_id} has no birth_input")
    resolved_target_year = int(target_year or profile.get("target_year") or DEFAULT_TARGET_YEAR)
    if chart_builder is None:
        raise ValueError("V30 profile conversion requires a migration-only chart_builder")
    builder = chart_builder
    chart_payload = builder(profile, resolved_target_year)
    if chart_payload.get("status") != "ready":
        raise ValueError(f"V30 profile {source_profile_id} chart build is not ready")
    pillars = chart_payload.get("pillars")
    if not isinstance(pillars, Mapping):
        raise ValueError(f"V30 profile {source_profile_id} chart build has no pillars")

    year_stem, year_branch = _split_pillar(pillars.get("year"))
    month_stem, month_branch = _split_pillar(pillars.get("month"))
    day_stem, day_branch = _split_pillar(pillars.get("day"))
    hour_stem, hour_branch = _split_pillar(pillars.get("hour"))
    gender = _v30_gender_to_v40(str(birth_payload.get("gender") or ""))
    profile_id = f"v30-admin:{source_profile_id}"
    chart = BaziChartFacts(
        chart_id=f"chart:{profile_id}",
        gender=gender,
        year_stem=year_stem,
        year_branch=year_branch,
        month_stem=month_stem,
        month_branch=month_branch,
        day_stem=day_stem,
        day_branch=day_branch,
        hour_stem=hour_stem,
        hour_branch=hour_branch,
        current_luck=str(chart_payload.get("current_luck") or ""),
        current_year=str(chart_payload.get("current_year") or ""),
        source="imported_from_v30_admin_profile",
    )
    birth_input = BirthInputCanonical(
        input_id=f"birth:{profile_id}",
        calendar_type=str(birth_payload.get("calendar_type") or "solar"),
        birth_date=str(birth_payload.get("birth_date") or ""),
        birth_time=str(birth_payload.get("birth_time") or ""),
        gender=gender,
        timezone=str(birth_payload.get("timezone") or "Asia/Shanghai"),
        location=str(birth_payload.get("birth_place") or ""),
        leap_month=bool(birth_payload.get("lunar_is_leap_month") or False),
        source="imported_from_v30_admin_profile",
    )
    ziwei = ZiweiChartFacts(
        chart_id=f"ziwei:{profile_id}",
        life_palace="待校准",
        body_palace="待校准",
        decade_luck=chart.current_luck,
        flow_year=chart.current_year,
        domain_lenses={
            "overview": "V30 admin 档案已迁入，紫微作为旁路校准线索保留。",
            "hidden_attribute": "保留反复出现但八字表层不容易直接解释的经历，进入 Probe 校准。",
        },
        source="v30_admin_profile_sidecar_placeholder",
    )
    return BaziProfileRecord(
        profile_id=profile_id,
        user_id=user_id,
        display_name=str(profile.get("display_name") or source_profile_id),
        gender=gender,
        chart_facts=chart,
        birth_input=birth_input,
        ziwei_chart_facts=ziwei,
        is_default=is_default,
        tags=["v30_admin_import", str(profile.get("status") or "active")],
    )


def sync_v30_admin_profiles_to_repository(
    *,
    repository: V40PostgresRepository,
    source_store_path: Path,
    chart_builder: ChartBuilder | None = None,
) -> AdminProfileSyncResult:
    store = load_v30_product_store(source_store_path)
    admin_account = build_admin_account()
    repository.save_user_account(admin_account)
    source_profiles = select_v30_admin_profiles(store)
    synced_profiles: list[dict[str, object]] = []
    skipped_profiles: list[dict[str, object]] = []
    for index, source_profile in enumerate(source_profiles):
        try:
            profile = convert_v30_profile_to_v40(
                source_profile,
                user_id=admin_account.user_id,
                chart_builder=chart_builder,
                is_default=index == 0,
            )
            repository.save_bazi_profile(profile)
            synced_profiles.append(
                {
                    "profile_id": profile.profile_id,
                    "display_name": profile.display_name,
                    "pillars": profile.chart_facts.pillars_text,
                    "gender": profile.gender,
                }
            )
        except Exception as exc:
            skipped_profiles.append(
                {
                    "source_profile_id": str(source_profile.get("profile_id") or ""),
                    "display_name": str(source_profile.get("display_name") or ""),
                    "reason": str(exc),
                }
            )
    return AdminProfileSyncResult(
        version="v40.admin_v30_profile_sync_result.v1",
        admin_user=admin_account.public().model_dump(mode="json"),
        source_store=str(source_store_path),
        source_profile_count=len(source_profiles),
        synced_profile_count=len(synced_profiles),
        skipped_profile_count=len(skipped_profiles),
        synced_profiles=synced_profiles,
        skipped_profiles=skipped_profiles,
    )


def _split_pillar(value: object) -> tuple[str, str]:
    text = str(value or "").strip()
    if len(text) < 2:
        raise ValueError(f"Invalid pillar: {text}")
    return text[:1], text[1:2]


def _v30_gender_to_v40(value: str) -> str:
    gender = value.strip().lower()
    if gender in {"female", "坤", "女"}:
        return "坤"
    if gender in {"male", "乾", "男"}:
        return "乾"
    return ""
