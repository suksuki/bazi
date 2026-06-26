from __future__ import annotations

import os
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterator

from v30.knowledge.library import KRP_LIBRARY_UNITS
from v30.knowledge.packs.multidimensional_taxonomy import MACRO_DIMENSIONS
from v30.knowledge.source_registry import SOURCE_FAMILIES
from v30.rules.evidence import RULE_EVIDENCE_SPECS
from v30.runtime import create_smoke_runtime
from v30.storage.m3 import write_m3_snapshot_to_postgres
from v30.validation import run_518k_validation, run_synthetic_tier
from v30.validation.m3_source_governed_calibration import build_m3_source_governed_calibration


def build_m3_core_spine_snapshot(
    *,
    include_518k_sample: bool = False,
    sample_limit: int = 8,
) -> dict[str, object]:
    runtime = create_smoke_runtime("m3-core-spine-snapshot")
    policy_effect = runtime.question_plan.policy_effect
    krp_units = [row.model_dump(mode="json") for row in KRP_LIBRARY_UNITS]
    rule_specs = [row.model_dump(mode="json") for row in RULE_EVIDENCE_SPECS]
    portrait_assets = _portrait_assets()
    synthetic = run_synthetic_tier("m3_core_spine")
    snapshot: dict[str, object] = {
        "version": "v30.m3_core_spine_snapshot.v1",
        "snapshot_id": f"v30.m3.snapshot.{_timestamp_id()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inventory": _inventory(krp_units, rule_specs, portrait_assets),
        "missing_gaps": _missing_gaps(),
        "knowledge_units": krp_units,
        "rule_specs": rule_specs,
        "portrait_assets": portrait_assets,
        "runtime_observation": {
            "reading_id": runtime.reading_id,
            "trace_id": runtime.trace_id,
            "feature_evidence_count": len(runtime.feature_evidence),
            "rule_evidence_count": sum(1 for row in runtime.feature_evidence if row.domain == "rule"),
            "krp_library_summary": policy_effect.get("krp_library_summary", {}),
            "macro_pack_summary": policy_effect.get("core_macro_pack_summary", {}),
            "macro_portrait_summary": policy_effect.get("macro_portrait_summary", {}),
            "structure_path_scores": runtime.structure_state.path_scores,
            "boundary": "m3_runtime_observation_does_not_mutate_chart_facts",
        },
        "synthetic_validation": {
            "suite_id": synthetic.suite_id,
            "passed": synthetic.passed,
            "case_count": synthetic.case_count,
            "passed_count": synthetic.passed_count,
            "failed_count": synthetic.failed_count,
        },
        "validation_518k": {
            "included": False,
            "reason": "not_requested",
        },
        "storage_boundary": "m3_snapshot_persists_support_data_without_promoting_policy_or_mutating_chart_facts",
    }
    sample = None
    if include_518k_sample:
        sample = run_518k_validation(mode="sample", limit=sample_limit)
        snapshot["validation_518k"] = {
            "included": True,
            "run_id": sample.run_id,
            "mode": sample.mode,
            "case_count": sample.case_count,
            "promotion_signal": sample.promotion_signal,
            "artifact_record_id": sample.artifact_record_id,
            "artifact_search_backend": sample.artifact_search_backend,
            "coverage_metrics": sample.coverage_metrics,
            "drift_metrics": sample.drift_metrics,
        }
    snapshot["source_governed_calibration"] = build_m3_source_governed_calibration(
        krp_units=krp_units,
        rule_specs=rule_specs,
        portrait_assets=portrait_assets,
        synthetic=synthetic,
        validation_518k=sample,
    )
    return snapshot


def run_m3_core_spine_snapshot(
    *,
    include_518k_sample: bool = False,
    sample_limit: int = 8,
    write_db: bool = True,
    artifact_dir: str | Path | None = None,
) -> dict[str, object]:
    with _local_snapshot_build_env():
        snapshot = build_m3_core_spine_snapshot(
            include_518k_sample=include_518k_sample,
            sample_limit=sample_limit,
        )
    if artifact_dir is not None:
        artifact_path = _write_artifact(snapshot, Path(artifact_dir))
        snapshot["artifact_uri"] = str(artifact_path)
    if write_db:
        write = write_m3_snapshot_to_postgres(snapshot)
        snapshot["db_write"] = write.model_dump(mode="json")
    return snapshot


def _inventory(
    krp_units: list[dict[str, object]],
    rule_specs: list[dict[str, object]],
    portrait_assets: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "krp_unit_count": len(krp_units),
        "krp_unit_type_counts": dict(Counter(str(row.get("unit_type") or "") for row in krp_units)),
        "krp_domains": sorted({str(row.get("domain") or "") for row in krp_units if row.get("domain")}),
        "rule_spec_count": len(rule_specs),
        "rule_domains": sorted({str(row.get("domain") or "") for row in rule_specs if row.get("domain")}),
        "source_family_count": len(SOURCE_FAMILIES),
        "source_family_ids": sorted(row.source_family_id for row in SOURCE_FAMILIES),
        "macro_dimension_count": len(MACRO_DIMENSIONS),
        "macro_domains": sorted({row.domain for row in MACRO_DIMENSIONS}),
        "portrait_asset_count": len(portrait_assets),
        "portrait_dimension_count": len({
            dimension
            for row in krp_units
            for dimension in _string_list(row.get("portrait_dimensions"))
        }),
        "portrait_tag_count": len({
            tag
            for row in krp_units
            for tag in _string_list(row.get("portrait_tags"))
        }),
    }


def _portrait_assets() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dimension in MACRO_DIMENSIONS:
        payload = dimension.model_dump(mode="json")
        rows.append({
            "asset_id": dimension.dimension_id,
            "asset_type": "macro_dimension",
            "domain": dimension.domain,
            "payload": payload,
            **payload,
        })
    return rows


def _missing_gaps() -> list[dict[str, object]]:
    return [
        {
            "gap_id": "m3.real_case_calibration_tags",
            "status": "active_gap",
            "description": "Need more canonical real-case tags mapped to K/R/P, rule states, dynamic paths, and portrait density.",
        },
        {
            "gap_id": "m3.domain_rule_depth_expansion",
            "status": "active_gap",
            "description": "Wealth, career, relationship, romance, and health rules are bounded but need deeper calibrated subfamilies.",
        },
        {
            "gap_id": "m3.training_synthetic_distribution",
            "status": "g1_tagged",
            "description": "M3-G1 records training and synthetic distribution tags before any K/R/P or rule-weight tuning.",
        },
        {
            "gap_id": "m3.source_extraction_queue",
            "status": "g1_tagged",
            "description": "M3-G1 records source-governed extraction queue tags from source registry records, not runtime imports.",
        },
        {
            "gap_id": "m3.518k_distribution_summary",
            "status": "g1_tagged",
            "description": "M3-G1 records 518K distribution evidence when requested; full 518K remains explicit-only.",
        },
    ]


def _write_artifact(snapshot: dict[str, object], artifact_dir: Path) -> Path:
    import json

    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{snapshot['snapshot_id']}.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


@contextmanager
def _local_snapshot_build_env() -> Iterator[None]:
    previous_repository = os.environ.get("V30_REPOSITORY")
    previous_database_url = os.environ.get("V30_DATABASE_URL")
    os.environ["V30_REPOSITORY"] = "memory"
    os.environ.pop("V30_DATABASE_URL", None)
    try:
        yield
    finally:
        if previous_repository is None:
            os.environ.pop("V30_REPOSITORY", None)
        else:
            os.environ["V30_REPOSITORY"] = previous_repository
        if previous_database_url is None:
            os.environ.pop("V30_DATABASE_URL", None)
        else:
            os.environ["V30_DATABASE_URL"] = previous_database_url
