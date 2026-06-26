from __future__ import annotations

import csv
import json
import os
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field

from v30.config import load_settings
from v30.contracts import V30Model
from v30.runtime import create_smoke_runtime
from v30.storage.artifacts import artifact_record_id_for_518k, index_518k_validation_artifact


CorpusMode = Literal["sample", "shard", "full"]
TARGET_CASE_COUNT = 518_400
DEFAULT_SHARD_COUNT = 128
DEFAULT_BATCH_SIZE = 512


class CorpusCaseSummary(V30Model):
    case_id: str
    shard_id: int
    day_master: str
    mainline_quality_gate: str
    question_count: int
    top_question_id: str
    hidden_factor_probe_count: int
    knowledge_rule_portrait_signal_count: int
    model_signal_summary_present: bool = False
    interaction_state_present: bool = False
    visible_next_question_id: str = ""
    internal_next_question_id: str = ""
    visible_internal_split: bool = False
    calibration_probe_user_visible: bool = False
    source: str = "generated"
    source_row_id: str | None = None


class CorpusSourceCase(V30Model):
    source_row_id: str
    day_master: str
    day_master_element: str = "wood"
    locale: str = "zh"
    luck_pillar: str = ""
    flow_year_pillar: str = ""
    hidden_factor_user_calibrated: bool = False
    useful_god_path_resolved: bool = False
    branch_single_factor_confirmed: bool = False


class Corpus518KValidationResult(V30Model):
    run_id: str
    mode: CorpusMode
    corpus_version: str
    target_case_count: int = TARGET_CASE_COUNT
    shard_count: int = DEFAULT_SHARD_COUNT
    shard_ids: list[int] = Field(default_factory=list)
    case_count: int
    coverage_metrics: dict[str, object]
    drift_metrics: dict[str, object]
    failure_clusters: list[dict[str, object]] = Field(default_factory=list)
    promotion_signal: str
    artifact_uri: str | None = None
    index_uri: str | None = None
    index_entry_uri: str | None = None
    artifact_record_id: str | None = None
    artifact_search_backend: str = "json_fallback"
    artifact_searchable: bool = False
    case_summaries: list[CorpusCaseSummary] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime


def run_518k_validation(
    *,
    mode: CorpusMode = "sample",
    limit: int | None = None,
    shard_id: int | None = None,
    confirm_full: bool = False,
    source_path: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> Corpus518KValidationResult:
    if mode == "full" and not confirm_full:
        raise ValueError("full 518K validation requires confirm_full=True")
    started_at = datetime.now(timezone.utc)
    effective_limit = _effective_limit(mode, limit)
    shard_ids = _shard_ids(mode, shard_id)
    source_cases = list(_load_source_cases(source_path, limit=effective_limit)) if source_path else []
    if source_cases:
        summaries = [
            _case_summary_from_source(
                row,
                index,
                shard_ids[index % len(shard_ids)],
                policy_payload_overrides=policy_payload_overrides,
                active_policy_version_overrides=active_policy_version_overrides,
            )
            for index, row in enumerate(source_cases)
        ]
        corpus_version = f"v30.external_source.{Path(source_path).name}.v1"
    else:
        summaries = [
            _case_summary(
                index,
                shard_ids[index % len(shard_ids)],
                policy_payload_overrides=policy_payload_overrides,
                active_policy_version_overrides=active_policy_version_overrides,
            )
            for index in range(effective_limit)
        ]
        corpus_version = "v30.generated_518k_contract.v1"
    finished_at = datetime.now(timezone.utc)
    failures = _failure_clusters(summaries)
    result = Corpus518KValidationResult(
        run_id=f"v30.518k.{mode}.{started_at.strftime('%Y%m%d%H%M%S%f')}",
        mode=mode,
        corpus_version=corpus_version,
        shard_ids=shard_ids,
        case_count=len(summaries),
        coverage_metrics=_coverage_metrics(summaries),
        drift_metrics=_drift_metrics(summaries),
        failure_clusters=failures,
        promotion_signal="eligible" if not failures else "blocked",
        case_summaries=summaries,
        started_at=started_at,
        finished_at=finished_at,
    )
    return _persist_validation_artifact(result, artifact_dir)


def _persist_validation_artifact(
    result: Corpus518KValidationResult,
    artifact_dir: str | Path | None,
) -> Corpus518KValidationResult:
    root = _artifact_root(artifact_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{result.run_id}.json"
    result = result.model_copy(
        update={
            "artifact_uri": str(path),
            "artifact_record_id": artifact_record_id_for_518k(result.run_id),
        }
    )
    index_uris = _persist_validation_index(result, root)
    result = result.model_copy(update=index_uris)
    search_meta = index_518k_validation_artifact(result)
    result = result.model_copy(
        update={
            "artifact_record_id": search_meta.artifact_record_id,
            "artifact_search_backend": search_meta.artifact_search_backend,
            "artifact_searchable": search_meta.artifact_searchable,
        }
    )
    _persist_validation_index(result, root)
    path.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _persist_validation_index(result: Corpus518KValidationResult, root: Path) -> dict[str, str]:
    index_dir = root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    entry_path = index_dir / f"{result.run_id}.index.json"
    index_path = root / "index.json"
    entry = _validation_index_entry(result, entry_path)
    entry_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    existing = _load_validation_index(index_path)
    entries = [
        row
        for row in existing.get("entries", [])
        if isinstance(row, dict) and row.get("run_id") != result.run_id
    ]
    entries.append(entry)
    entries = sorted(entries, key=lambda row: str(row.get("started_at", "")))
    latest_by_mode: dict[str, str] = {}
    for row in entries:
        mode = str(row.get("mode") or "")
        run_id = str(row.get("run_id") or "")
        if mode and run_id:
            latest_by_mode[mode] = run_id
    index = {
        "index_id": "v30.518k.validation_index.v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "run_count": len(entries),
        "latest_run_id_by_mode": latest_by_mode,
        "entries": entries,
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"index_uri": str(index_path), "index_entry_uri": str(entry_path)}


def _validation_index_entry(result: Corpus518KValidationResult, entry_path: Path) -> dict[str, object]:
    return {
        "run_id": result.run_id,
        "mode": result.mode,
        "corpus_version": result.corpus_version,
        "target_case_count": result.target_case_count,
        "shard_count": result.shard_count,
        "shard_ids": result.shard_ids,
        "case_count": result.case_count,
        "promotion_signal": result.promotion_signal,
        "failure_cluster_count": len(result.failure_clusters),
        "artifact_uri": result.artifact_uri,
        "artifact_record_id": result.artifact_record_id,
        "artifact_search_backend": result.artifact_search_backend,
        "artifact_searchable": result.artifact_searchable,
        "index_entry_uri": str(entry_path),
        "coverage_metrics": result.coverage_metrics,
        "drift_metrics": result.drift_metrics,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
    }


def _load_validation_index(index_path: Path) -> dict[str, object]:
    if not index_path.exists():
        return {}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _artifact_root(artifact_dir: str | Path | None) -> Path:
    if artifact_dir is not None:
        return Path(artifact_dir)
    env_dir = os.environ.get("V30_518K_ARTIFACT_DIR")
    if env_dir:
        return Path(env_dir)
    return load_settings().runtime_dir / "validation" / "518k"


def _effective_limit(mode: CorpusMode, limit: int | None) -> int:
    if limit is not None:
        return max(1, limit)
    if mode == "sample":
        return 8
    if mode == "shard":
        return DEFAULT_BATCH_SIZE
    return TARGET_CASE_COUNT


def _shard_ids(mode: CorpusMode, shard_id: int | None) -> list[int]:
    if mode == "sample":
        return [0]
    if mode == "shard":
        return [0 if shard_id is None else shard_id]
    return list(range(DEFAULT_SHARD_COUNT))


def _case_summary(
    index: int,
    shard_id: int,
    *,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> CorpusCaseSummary:
    day_master = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")[index % 10]
    runtime = create_smoke_runtime(
        reading_id=f"v30-518k-{shard_id}-{index}",
        day_master=day_master,
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
    interaction_state = runtime.question_plan.policy_effect.get("interaction_state", {})
    interaction_state = interaction_state if isinstance(interaction_state, dict) else {}
    visible_next = str(interaction_state.get("visible_next_question_id") or "")
    internal_next = str(interaction_state.get("internal_next_question_id") or "")
    return CorpusCaseSummary(
        case_id=f"v30.generated_518k.{shard_id}.{index}",
        shard_id=shard_id,
        day_master=day_master,
        mainline_quality_gate=runtime.mainline_state.quality_gate,
        question_count=len(runtime.question_plan.recommended_questions),
        top_question_id=str(runtime.question_plan.recommended_questions[0]["question_id"]),
        hidden_factor_probe_count=len(runtime.question_plan.hidden_factor_probes),
        knowledge_rule_portrait_signal_count=len(runtime.question_plan.knowledge_rule_portrait_signals),
        model_signal_summary_present=bool(runtime.question_plan.policy_effect.get("model_signal_summary")),
        interaction_state_present=bool(interaction_state),
        visible_next_question_id=visible_next,
        internal_next_question_id=internal_next,
        visible_internal_split=bool(visible_next and internal_next and visible_next != internal_next),
        calibration_probe_user_visible=_is_calibration_probe_visible(visible_next, runtime.question_plan.recommended_questions),
    )


def _case_summary_from_source(
    row: CorpusSourceCase,
    index: int,
    shard_id: int,
    *,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> CorpusCaseSummary:
    runtime = create_smoke_runtime(
        reading_id=f"v30-518k-source-{shard_id}-{index}",
        day_master=row.day_master,
        day_master_element=row.day_master_element,
        locale=row.locale,
        luck_pillar=row.luck_pillar,
        flow_year_pillar=row.flow_year_pillar,
        hidden_factor_user_calibrated=row.hidden_factor_user_calibrated,
        useful_god_path_resolved=row.useful_god_path_resolved,
        branch_single_factor_confirmed=row.branch_single_factor_confirmed,
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
    interaction_state = runtime.question_plan.policy_effect.get("interaction_state", {})
    interaction_state = interaction_state if isinstance(interaction_state, dict) else {}
    visible_next = str(interaction_state.get("visible_next_question_id") or "")
    internal_next = str(interaction_state.get("internal_next_question_id") or "")
    return CorpusCaseSummary(
        case_id=f"v30.external_518k.{shard_id}.{index}",
        shard_id=shard_id,
        day_master=row.day_master,
        mainline_quality_gate=runtime.mainline_state.quality_gate,
        question_count=len(runtime.question_plan.recommended_questions),
        top_question_id=str(runtime.question_plan.recommended_questions[0]["question_id"]),
        hidden_factor_probe_count=len(runtime.question_plan.hidden_factor_probes),
        knowledge_rule_portrait_signal_count=len(runtime.question_plan.knowledge_rule_portrait_signals),
        model_signal_summary_present=bool(runtime.question_plan.policy_effect.get("model_signal_summary")),
        interaction_state_present=bool(interaction_state),
        visible_next_question_id=visible_next,
        internal_next_question_id=internal_next,
        visible_internal_split=bool(visible_next and internal_next and visible_next != internal_next),
        calibration_probe_user_visible=_is_calibration_probe_visible(visible_next, runtime.question_plan.recommended_questions),
        source="external",
        source_row_id=row.source_row_id,
    )


def _load_source_cases(source_path: str | Path, *, limit: int) -> Iterator[CorpusSourceCase]:
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"518K source path does not exist: {path}")
    if path.suffix.lower() == ".jsonl":
        yield from _load_jsonl_source_cases(path, limit=limit)
        return
    if path.suffix.lower() == ".csv":
        yield from _load_csv_source_cases(path, limit=limit)
        return
    raise ValueError("518K source path must be .jsonl or .csv")


def _load_jsonl_source_cases(path: Path, *, limit: int) -> Iterator[CorpusSourceCase]:
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= limit:
                break
            payload = json.loads(line)
            yield _source_case_from_payload(payload, default_id=f"{path.stem}:{index}")


def _load_csv_source_cases(path: Path, *, limit: int) -> Iterator[CorpusSourceCase]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        for index, payload in enumerate(csv.DictReader(handle)):
            if index >= limit:
                break
            yield _source_case_from_payload(payload, default_id=f"{path.stem}:{index}")


def _source_case_from_payload(payload: dict[str, object], *, default_id: str) -> CorpusSourceCase:
    return CorpusSourceCase(
        source_row_id=str(payload.get("source_row_id") or payload.get("case_id") or default_id),
        day_master=str(payload.get("day_master") or "甲"),
        day_master_element=str(payload.get("day_master_element") or "wood"),
        locale=str(payload.get("locale") or "zh"),
        luck_pillar=str(payload.get("luck_pillar") or ""),
        flow_year_pillar=str(payload.get("flow_year_pillar") or ""),
        hidden_factor_user_calibrated=_coerce_bool(payload.get("hidden_factor_user_calibrated")),
        useful_god_path_resolved=_coerce_bool(payload.get("useful_god_path_resolved")),
        branch_single_factor_confirmed=_coerce_bool(payload.get("branch_single_factor_confirmed")),
    )


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _coverage_metrics(summaries: list[CorpusCaseSummary]) -> dict[str, object]:
    day_masters = sorted({row.day_master for row in summaries})
    top_questions = sorted({row.top_question_id for row in summaries})
    return {
        "day_master_count": len(day_masters),
        "day_masters": day_masters,
        "top_question_ids": top_questions,
        "hidden_factor_probe_coverage": sum(1 for row in summaries if row.hidden_factor_probe_count > 0),
        "krp_signal_coverage": sum(1 for row in summaries if row.knowledge_rule_portrait_signal_count > 0),
        "question_recommendation_coverage": sum(1 for row in summaries if row.question_count > 0),
        "model_signal_summary_coverage": sum(1 for row in summaries if row.model_signal_summary_present),
        "interaction_state_coverage": sum(1 for row in summaries if row.interaction_state_present),
        "visible_internal_next_question_split_count": sum(1 for row in summaries if row.visible_internal_split),
        "calibration_probe_user_visible_count": sum(1 for row in summaries if row.calibration_probe_user_visible),
        "external_source_count": sum(1 for row in summaries if row.source == "external"),
    }


def _drift_metrics(summaries: list[CorpusCaseSummary]) -> dict[str, object]:
    unsupported_question_count = sum(1 for row in summaries if not row.top_question_id)
    weak_signal_count = sum(1 for row in summaries if row.knowledge_rule_portrait_signal_count < 3)
    missing_model_signal_count = sum(1 for row in summaries if not row.model_signal_summary_present)
    missing_interaction_state_count = sum(1 for row in summaries if not row.interaction_state_present)
    calibration_leak_count = sum(1 for row in summaries if row.calibration_probe_user_visible)
    return {
        "unsupported_question_rate": round(unsupported_question_count / max(1, len(summaries)), 4),
        "weak_krp_signal_rate": round(weak_signal_count / max(1, len(summaries)), 4),
        "missing_model_signal_summary_rate": round(missing_model_signal_count / max(1, len(summaries)), 4),
        "missing_interaction_state_rate": round(missing_interaction_state_count / max(1, len(summaries)), 4),
        "calibration_probe_user_visible_rate": round(calibration_leak_count / max(1, len(summaries)), 4),
    }


def _failure_clusters(summaries: list[CorpusCaseSummary]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    if any(row.question_count == 0 for row in summaries):
        failures.append({"cluster_key": "missing_question_recommendations", "severity": "high"})
    if any(row.knowledge_rule_portrait_signal_count < 3 for row in summaries):
        failures.append({"cluster_key": "weak_krp_signal_coverage", "severity": "medium"})
    if any(row.calibration_probe_user_visible for row in summaries):
        failures.append({"cluster_key": "calibration_probe_visible_to_user", "severity": "high"})
    return failures


def _is_calibration_probe_visible(question_id: str, recommendations: list[dict[str, object]]) -> bool:
    if not question_id:
        return False
    for row in recommendations:
        if str(row.get("question_id")) != question_id:
            continue
        return str(row.get("interaction_type") or "") == "calibration_probe"
    return False
