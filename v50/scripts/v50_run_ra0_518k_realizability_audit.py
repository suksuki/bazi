from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import resource
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

from core.audit.calendar_realizability import (
    BOUNDARY_RANGE_EDGE,
    BOUNDARY_SOLAR_TERM,
    BOUNDARY_ZI_ROLLOVER,
    CalendarScanResult,
    boundary_labels,
    datetime_from_civil_minute,
    default_audit_ranges,
    scan_calendar_realizability,
)
from core.audit.chart_universe import (
    UNIVERSE_SIZE,
    StructuralUniverseAudit,
    audit_structural_universe,
    chart_index,
    chart_key,
    pillars_at_index,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / ".runtime" / "validation" / "ra0-518k-realizability-v1"
AUDIT_VERSION = "v50.ra0_518k_chart_realizability_audit.v1"
CLASSIFICATION_SCHEMA_VERSION = "v50.ra0_518k_classification.v1"
FIXTURE_PATH = ROOT / "data/validation/fixtures/ra0_518k_realizability_v1.json"

SOURCE_PATHS = (
    ROOT / "packages/core/audit/chart_universe.py",
    ROOT / "packages/core/audit/calendar_realizability.py",
    ROOT / "packages/core/engines/bazi/chart_constraints.py",
    ROOT / "packages/core/engines/bazi/pillar_cycle.py",
    ROOT / "packages/core/engines/bazi/temporal_service.py",
    ROOT / "packages/core/engines/birth_calendar.py",
    FIXTURE_PATH,
    ROOT / "tests/test_v50_ra0_518k_realizability_audit.py",
    Path(__file__).resolve(),
)


def run_audit(
    *,
    output_root: Path,
    legacy_generator: Path | None = None,
    legacy_index: Path | None = None,
    timezone: str = "Asia/Shanghai",
    compare_against: Path | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    started = perf_counter()

    structural_started = perf_counter()
    structural = audit_structural_universe()
    structural_seconds = perf_counter() - structural_started
    _require_structural_reconciliation(structural)

    calendar_started = perf_counter()
    calendar = scan_calendar_realizability(
        list(default_audit_ranges()),
        timezone=timezone,
    )
    calendar_seconds = perf_counter() - calendar_started
    if calendar.actual_timestamp_structural_failure_count:
        raise RuntimeError("actual_timestamp_generated_structurally_invalid_chart")

    source_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in SOURCE_PATHS
    }
    legacy = inspect_legacy_518k(
        generator_path=legacy_generator,
        index_path=legacy_index,
    )
    policy_payload = {
        **calendar.policy,
        "formal_source_sha256": {
            key: value
            for key, value in source_hashes.items()
            if "/engines/" in key
        },
    }
    policy_hash = sha256_json(policy_payload)

    output_started = perf_counter()
    classification_path = output_root / "ra0_518k_classification_v1.jsonl.gz"
    write_deterministic_gzip_jsonl(
        classification_path,
        classification_rows(calendar, policy_hash),
    )
    boundary_path = output_root / "ra0_518k_boundary_evidence_v1.json"
    write_json(boundary_path, {
        "schema_version": "v50.ra0_518k_boundary_evidence.v1",
        "policy_hash": policy_hash,
        "samples": calendar.boundary_samples,
        "sample_count": len(calendar.boundary_samples),
        "samples_are_representative_not_exhaustive": True,
    })
    anomaly_path = output_root / "ra0_518k_structural_anomalies_v1.json"
    fixture_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    write_json(anomaly_path, {
        "schema_version": "v50.ra0_518k_structural_anomalies.v1",
        "reconstructed_universe_invalid_count": structural.structurally_invalid_count,
        "reconstructed_universe_invalid_reason_distribution": structural.invalid_reason_distribution,
        "negative_fixtures": fixture_payload["structural_negative_fixtures"],
        "boundary_fixtures": fixture_payload["boundary_fixtures"],
        "original_518k_deleted_or_modified": False,
    })

    semantic_summary = build_semantic_summary(
        structural=structural,
        calendar=calendar,
        legacy=legacy,
        policy_payload=policy_payload,
        policy_hash=policy_hash,
        source_hashes=source_hashes,
    )
    semantic_summary_path = output_root / "ra0_518k_semantic_summary_v1.json"
    write_json(semantic_summary_path, semantic_summary)

    deterministic_hashes = {
        classification_path.name: sha256_file(classification_path),
        boundary_path.name: sha256_file(boundary_path),
        anomaly_path.name: sha256_file(anomaly_path),
        semantic_summary_path.name: sha256_file(semantic_summary_path),
    }
    determinism = compare_deterministic_outputs(
        deterministic_hashes,
        compare_against=compare_against,
    )
    output_seconds = perf_counter() - output_started
    total_seconds = perf_counter() - started

    execution_summary = {
        "audit_version": AUDIT_VERSION,
        "status": (
            semantic_summary["status"]
            if determinism["status"] != "FAIL"
            else "FAIL"
        ),
        "semantic_summary": semantic_summary,
        "performance": {
            "structural_audit_seconds": round(structural_seconds, 6),
            "calendar_scan_seconds": round(calendar_seconds, 6),
            "output_generation_seconds": round(output_seconds, 6),
            "pure_compute_seconds": round(structural_seconds + calendar_seconds, 6),
            "total_elapsed_seconds": round(total_seconds, 6),
            "peak_rss_bytes": peak_rss_bytes(),
        },
        "determinism": determinism,
        "output_hashes": deterministic_hashes,
    }
    execution_summary_path = output_root / "ra0_518k_execution_summary_v1.json"
    write_json(execution_summary_path, execution_summary)

    report_path = output_root / "RA0_518K_CHART_REALIZABILITY_AUDIT_V1.md"
    report_path.write_text(render_markdown(execution_summary), encoding="utf-8")

    manifest_outputs = {
        path.name: {"size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (
            classification_path,
            boundary_path,
            anomaly_path,
            semantic_summary_path,
            execution_summary_path,
            report_path,
        )
    }
    manifest = {
        "manifest_version": "v50.ra0_518k_run_manifest.v1",
        "audit_version": AUDIT_VERSION,
        "command": reproducible_command(
            output_root=output_root,
            legacy_generator=legacy_generator,
            legacy_index=legacy_index,
            timezone=timezone,
        ),
        "parameters": {
            "timezone": timezone,
            "ranges": [item.definition.as_dict() for item in calendar.ranges.values()],
            "legacy_generator": str(legacy_generator) if legacy_generator else None,
            "legacy_index": str(legacy_index) if legacy_index else None,
        },
        "source_hashes": source_hashes,
        "policy_hash": policy_hash,
        "outputs": manifest_outputs,
        "determinism": determinism,
        "boundaries": {
            "read_only": True,
            "llm_used": False,
            "formal_algorithm_modified": False,
            "database_migration": False,
            "legacy_518k_deleted_or_overwritten": False,
        },
    }
    manifest_path = output_root / "ra0_518k_run_manifest_v1.json"
    write_json(manifest_path, manifest)
    return {
        **execution_summary,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "report_path": str(report_path),
        "output_root": str(output_root),
    }


def classification_rows(
    calendar: CalendarScanResult,
    policy_hash: str,
) -> Iterator[dict[str, Any]]:
    range_ids = tuple(calendar.ranges)
    for index in range(UNIVERSE_SIZE):
        pillars = pillars_at_index(index)
        realizability: dict[str, bool] = {}
        classifications: dict[str, str] = {}
        witnesses: dict[str, str | None] = {}
        boundary_status: dict[str, list[str]] = {}
        for range_id in range_ids:
            accumulator = calendar.ranges[range_id]
            realized = bool(accumulator.realizable[index])
            realizability[range_id] = realized
            classifications[range_id] = (
                "CALENDAR_REALIZABLE" if realized else "UNSEEN_IN_RANGE"
            )
            witness = accumulator.first_witness_minute[index]
            witnesses[range_id] = (
                datetime_from_civil_minute(witness).isoformat()
                if witness >= 0
                else None
            )
            boundary_status[range_id] = boundary_labels(accumulator.boundary_flags[index])
        yield {
            "schema_version": CLASSIFICATION_SCHEMA_VERSION,
            "chart_key": chart_key(pillars),
            "structural_validity": "STRUCTURALLY_VALID",
            "invalid_reason": None,
            "calendar_range": list(range_ids),
            "calendar_realizable": realizability,
            "range_classification": classifications,
            "first_witness_timestamp": witnesses,
            "boundary_status": boundary_status,
            "temporal_policy_version": policy_hash,
        }


def build_semantic_summary(
    *,
    structural: StructuralUniverseAudit,
    calendar: CalendarScanResult,
    legacy: dict[str, Any],
    policy_payload: dict[str, Any],
    policy_hash: str,
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    ranges: dict[str, Any] = {}
    for range_id, accumulator in calendar.ranges.items():
        ranges[range_id] = {
            **accumulator.definition.as_dict(),
            "calendar_realizable_count": accumulator.realizable_count,
            "unseen_in_range_count": accumulator.unseen_count,
            "boundary_ambiguous_chart_count": accumulator.boundary_ambiguous_chart_count,
            "solar_term_boundary_chart_count": accumulator.boundary_count(BOUNDARY_SOLAR_TERM),
            "zi_rollover_policy_sensitive_chart_count": accumulator.boundary_count(BOUNDARY_ZI_ROLLOVER),
            "range_edge_sensitive_chart_count": accumulator.boundary_count(BOUNDARY_RANGE_EDGE),
            "solar_term_boundary_event_count": accumulator.solar_term_boundary_event_count,
            "zi_rollover_policy_event_count": accumulator.zi_rollover_policy_event_count,
            "timestamp_observation_count": accumulator.timestamp_observation_count,
            "representative_witnesses": representative_witnesses(accumulator),
        }

    all_extended = ranges["extended_4_jiazi_1804_2044"]["unseen_in_range_count"] == 0
    return {
        "audit_version": AUDIT_VERSION,
        "status": (
            "PASS_WITH_BOUNDARY_FINDING"
            if calendar.canonical_raw_late_zi_invalid_count
            else "PASS"
        ),
        "legacy_518k_discovery": legacy,
        "reconstructed_universe": {
            **asdict(structural),
            "formula": "60 year pillars x 12 legal solar months x 60 day pillars x 12 legal double-hours",
            "formula_expression": "60*12*60*12",
            "formal_five_tigers_applied": True,
            "formal_five_rats_applied": True,
            "schema": {
                "chart_key": "year|month|day|hour",
                "pillar_count": 4,
                "index_order": "year,legal_month_for_year,day,legal_hour_for_day",
            },
        },
        "calendar_forward_scan": {
            "method": "daily canonical year-month-day resolution plus twelve formal hour derivations; Jie dates split at canonical minute; no reverse per-chart lookup",
            "valid_chart_key_representation": "canonical_indexed_bitmap_set",
            "calendar_days_scanned": calendar.calendar_days_scanned,
            "canonical_resolution_call_count": calendar.canonical_resolution_call_count,
            "annual_authority_crosscheck_count": calendar.annual_authority_crosscheck_count,
            "actual_timestamp_structural_failure_count": calendar.actual_timestamp_structural_failure_count,
            "canonical_raw_late_zi_invalid_count": calendar.canonical_raw_late_zi_invalid_count,
            "canonical_raw_late_zi_invalid_samples": calendar.canonical_raw_late_zi_invalid_samples,
            "jie_boundary_count": calendar.jie_boundary_count,
            "ranges": ranges,
        },
        "temporal_policy": policy_payload,
        "temporal_policy_hash": policy_hash,
        "source_hashes": source_hashes,
        "conclusions": {
            "structurally_impossible_inside_reconstructed_518k": structural.structurally_invalid_count,
            "unseen_is_not_structurally_invalid": True,
            "all_reconstructed_charts_realizable_across_four_jiazi_cycles": all_extended,
            "positive_pool_exclusion": "exclude STRUCTURALLY_INVALID; range-scoped UNSEEN may not be used as positive witnesses for that range",
            "negative_fixture_retention": "retain explicit structural-rule counterexamples and boundary-policy divergences",
            "theoretical_candidate_retention": "retain UNSEEN_IN_RANGE as theory candidates unless disproven structurally; never delete solely for nonappearance",
        },
    }


def inspect_legacy_518k(
    *,
    generator_path: Path | None,
    index_path: Path | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "entity_518k_file_found": False,
        "actual_entity_record_count": 0,
        "claimed_target_case_count": None,
        "legacy_generator_sha256": None,
        "legacy_index_sha256": None,
        "legacy_validation_run_count": 0,
        "legacy_validation_artifact_file_count": 0,
        "legacy_validation_artifact_size_bytes": 0,
        "legacy_schema_fields": [],
        "four_pillar_schema_present": False,
        "five_tigers_applied": False,
        "five_rats_applied": False,
        "finding": "no_entity_518k_corpus_located",
    }
    if generator_path and generator_path.is_file():
        source = generator_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        result["legacy_generator_sha256"] = sha256_file(generator_path)
        result["claimed_target_case_count"] = _ast_integer_assignment(tree, "TARGET_CASE_COUNT")
        result["legacy_schema_fields"] = _ast_model_fields(tree, "CorpusCaseSummary")
        result["four_pillar_schema_present"] = all(
            name in result["legacy_schema_fields"]
            for name in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")
        )
        result["five_tigers_applied"] = "FIVE_TIGERS" in source or "五虎遁" in source
        result["five_rats_applied"] = "FIVE_RATS" in source or "五鼠遁" in source
    if index_path and index_path.is_file():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
        result["legacy_index_sha256"] = sha256_file(index_path)
        result["legacy_validation_run_count"] = len(entries) if isinstance(entries, list) else 0
        root = index_path.parent
        files = [path for path in root.rglob("*") if path.is_file()]
        result["legacy_validation_artifact_file_count"] = len(files)
        result["legacy_validation_artifact_size_bytes"] = sum(path.stat().st_size for path in files)
    return result


def representative_witnesses(accumulator: Any, limit: int = 5) -> list[dict[str, str]]:
    preferred = (
        ("丁巳", "乙巳", "乙丑", "乙酉"),
        ("甲子", "丙寅", "甲子", "甲子"),
    )
    indices: list[int] = []
    for pillars in preferred:
        index = chart_index(pillars)
        if accumulator.realizable[index]:
            indices.append(index)
    for index, value in enumerate(accumulator.realizable):
        if value and index not in indices:
            indices.append(index)
        if len(indices) >= limit:
            break
    return [
        {
            "chart_key": chart_key(pillars_at_index(index)),
            "first_witness_timestamp": datetime_from_civil_minute(
                accumulator.first_witness_minute[index]
            ).isoformat(),
        }
        for index in indices[:limit]
    ]


def write_deterministic_gzip_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
            for row in rows:
                line = json.dumps(
                    row,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                compressed.write(line.encode("utf-8"))
                compressed.write(b"\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def compare_deterministic_outputs(
    current_hashes: dict[str, str],
    *,
    compare_against: Path | None,
) -> dict[str, Any]:
    if compare_against is None:
        return {"status": "NOT_REQUESTED", "compared_against": None, "matches": {}}
    expected = {
        name: sha256_file(compare_against / name)
        for name in current_hashes
        if (compare_against / name).is_file()
    }
    matches = {
        name: expected.get(name) == digest
        for name, digest in current_hashes.items()
    }
    return {
        "status": "PASS" if matches and all(matches.values()) else "FAIL",
        "compared_against": str(compare_against),
        "matches": matches,
        "expected_hashes": expected,
        "current_hashes": current_hashes,
    }


def render_markdown(execution: dict[str, Any]) -> str:
    semantic = execution["semantic_summary"]
    structural = semantic["reconstructed_universe"]
    scan = semantic["calendar_forward_scan"]
    legacy = semantic["legacy_518k_discovery"]
    ranges = scan["ranges"]
    performance = execution["performance"]
    lines = [
        "# RA0-518K Chart Realizability Audit v1",
        "",
        "> Read-only deterministic audit. No LLM, database migration, formal algorithm change, or source-corpus deletion.",
        "",
        "## Executive Finding",
        "",
        "The historical V30 `518K` implementation is a validation target contract, not an entity corpus of 518,400 four-pillar charts. Its generated rows rotate day masters and do not contain four pillars. RA0 therefore rebuilt the requested structural universe from the current formal V50 Jiazi, Five Tigers, and Five Rats rules, as explicitly authorized when no entity corpus exists.",
        "",
        "## Source Discovery",
        "",
        f"- Entity 518K corpus found: `{legacy['entity_518k_file_found']}`",
        f"- Actual entity rows found: `{legacy['actual_entity_record_count']}`",
        f"- Legacy claimed target count: `{legacy['claimed_target_case_count']}`",
        f"- Legacy validation runs: `{legacy['legacy_validation_run_count']}`",
        f"- Legacy artifact files: `{legacy['legacy_validation_artifact_file_count']}`",
        f"- Legacy four-pillar schema present: `{legacy['four_pillar_schema_present']}`",
        f"- Legacy Five Tigers / Five Rats applied: `{legacy['five_tigers_applied']} / {legacy['five_rats_applied']}`",
        "",
        "## Structural Reconciliation",
        "",
        f"- Formula: `{structural['formula_expression']}` = `{structural['record_count']}`",
        f"- Unique ChartKeys: `{structural['unique_chart_key_count']}`",
        f"- Duplicates: `{structural['duplicate_count']}`",
        f"- Structurally valid: `{structural['structurally_valid_count']}`",
        f"- Structurally invalid: `{structural['structurally_invalid_count']}`",
        f"- Universe content SHA-256: `{structural['content_sha256']}`",
        "",
        "## Calendar Realizability",
        "",
        "| Range | Realizable | Unseen in range | Boundary-sensitive charts |",
        "|---|---:|---:|---:|",
    ]
    for row in ranges.values():
        lines.append(
            f"| {row['label']} | {row['calendar_realizable_count']} | {row['unseen_in_range_count']} | {row['boundary_ambiguous_chart_count']} |"
        )
    lines.extend([
        "",
        f"- Calendar days scanned: `{scan['calendar_days_scanned']}`",
        f"- Canonical resolver calls: `{scan['canonical_resolution_call_count']}`",
        f"- Actual timestamp structural failures: `{scan['actual_timestamp_structural_failure_count']}`",
        f"- Canonical raw late-Zi rejections retained as boundary evidence: `{scan['canonical_raw_late_zi_invalid_count']}`",
        f"- Jie boundaries audited: `{scan['jie_boundary_count']}`",
        "",
        "`BOUNDARY_AMBIGUOUS` is recorded orthogonally in `boundary_status`; it never turns a structurally valid chart into `STRUCTURALLY_INVALID`.",
        "",
        "## Temporal Policy",
        "",
        f"- Policy hash: `{semantic['temporal_policy_hash']}`",
        f"- Calendar profile: `{semantic['temporal_policy']['calendar_profile']}`",
        f"- Formal day rollover: `{semantic['temporal_policy']['day_rollover_formal']}`",
        f"- Sensitivity policy: `{semantic['temporal_policy']['day_rollover_sensitivity']}`",
        f"- Timezone: `{semantic['temporal_policy']['timezone']}`",
        f"- True solar time: `{semantic['temporal_policy']['true_solar_time']}`",
        f"- Historical DST: `{semantic['temporal_policy']['historical_dst']}`",
        "",
        "## Performance",
        "",
        f"- Pure compute: `{performance['pure_compute_seconds']}` seconds",
        f"- Total elapsed: `{performance['total_elapsed_seconds']}` seconds",
        f"- Peak RSS: `{performance['peak_rss_bytes']}` bytes",
        f"- Deterministic rerun: `{execution['determinism']['status']}`",
        "",
        "## Classification Decision",
        "",
        "1. Structural impossibility is determined only by Jiazi, Five Tigers, and Five Rats failures, not by finite-range nonappearance.",
        "2. `UNSEEN_IN_RANGE` remains a range-scoped observation and is not deleted.",
        "3. Structurally invalid counterexamples and boundary-policy divergences remain Negative Fixtures.",
        "4. Structurally valid unseen rows remain theoretical synthetic candidates until stronger evidence exists.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "PYTHONPATH=packages:apps .runtime/venv/bin/python scripts/v50_run_ra0_518k_realizability_audit.py --output-root .runtime/validation/ra0-518k-realizability-v1",
        "```",
        "",
    ])
    return "\n".join(lines)


def reproducible_command(
    *,
    output_root: Path,
    legacy_generator: Path | None,
    legacy_index: Path | None,
    timezone: str,
) -> list[str]:
    command = [
        "PYTHONPATH=packages:apps",
        ".runtime/venv/bin/python",
        "scripts/v50_run_ra0_518k_realizability_audit.py",
        "--output-root",
        str(output_root),
        "--timezone",
        timezone,
    ]
    if legacy_generator:
        command.extend(["--legacy-generator", str(legacy_generator)])
    if legacy_index:
        command.extend(["--legacy-index", str(legacy_index)])
    return command


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _require_structural_reconciliation(result: StructuralUniverseAudit) -> None:
    if result.record_count != UNIVERSE_SIZE:
        raise RuntimeError("structural_universe_record_count_mismatch")
    if result.unique_chart_key_count + result.duplicate_count != result.record_count:
        raise RuntimeError("structural_universe_uniqueness_reconciliation_failed")
    if result.structurally_valid_count + result.structurally_invalid_count != result.record_count:
        raise RuntimeError("structural_universe_validity_reconciliation_failed")


def _ast_integer_assignment(tree: ast.AST, name: str) -> int | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name and isinstance(node.value, ast.Constant):
            return int(node.value.value)
    return None


def _ast_model_fields(tree: ast.AST, class_name: str) -> list[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            ]
    return []


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit 518K structural and calendar realizability")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--legacy-generator", type=Path)
    parser.add_argument("--legacy-index", type=Path)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--compare-against", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = run_audit(
        output_root=args.output_root.resolve(),
        legacy_generator=args.legacy_generator.resolve() if args.legacy_generator else None,
        legacy_index=args.legacy_index.resolve() if args.legacy_index else None,
        timezone=args.timezone,
        compare_against=args.compare_against.resolve() if args.compare_against else None,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if str(result["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
