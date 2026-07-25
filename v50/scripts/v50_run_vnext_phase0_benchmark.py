from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import MingliAgent, MingliContextCompiler, compile_chart_world
from core.mingli_agent.benchmark import (
    BenchmarkConditionalRole,
    CognitiveBenchmarkReading,
    benchmark_prompt,
    direct_power_user_prompt,
    project_cognitive_record,
)
from core.mingli_agent.fact_review import deterministic_fact_conflicts
from core.mingli_agent.phase0_governance import validate_frozen_formal_lock
from core.mingli_agent.reasoner import OllamaCognitiveModel


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_SET_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_development_set_v1.json"
DEVELOPMENT_FIXTURE_PACK_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_development_fixture_pack_v1.json"
MODEL_SELECTION_SET_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_model_policy_selection_set_v1.json"
MODEL_SELECTION_FIXTURE_PACK_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_model_policy_selection_fixture_pack_v1.json"
FORMAL_MANIFEST_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_sealed_formal_manifest_v1.json"
EXPERT_REFERENCE_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_expert_reference_space_v1.json"
REALITY_EVIDENCE_PATH = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_reality_evidence_v1.json"
TAXONOMY_PATH = ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v2.json"
HOLISTIC_SYNTHESIS_POLICY_PATH = ROOT / "config" / "vnext_phase0_holistic_synthesis_policy_v1.json"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "vnext-phase0-benchmark" / "v1"
LANES = (
    "direct_same_model",
    "direct_frontier",
    "current_v50",
    "fact_only_deepbazi",
    "holistic_synthesis",
    "vnext",
)
MODEL_POLICY_FAILURES = {
    "schema_output_truncated",
    "schema_failure",
    "model_timeout",
    "model_not_configured",
}
CRITICAL_PAIRWISE_LANE_PAIRS = (
    ("vnext", "current_v50"),
    ("vnext", "direct_frontier"),
    ("vnext", "holistic_synthesis"),
    ("vnext", "fact_only_deepbazi"),
    ("holistic_synthesis", "fact_only_deepbazi"),
    ("direct_same_model", "fact_only_deepbazi"),
)


class BenchmarkOnlyToolAnchoredCompiler(MingliContextCompiler):
    """Replays the old tool-anchored first look inside the benchmark only."""

    FACT_LIMITS = deepcopy(MingliContextCompiler.FACT_LIMITS)
    FACT_LIMITS["pattern"] = {
        "graph_relation": 12,
        "candidate_path": 5,
        "candidate_node_role": 5,
        "estimated_sensitivity": 4,
        "tool_salience": 4,
    }


def run_benchmark(
    *,
    run_id: str,
    live: bool,
    dry_run: bool,
    repeats: int,
    selected_lanes: list[str],
    base_url: str,
    same_model: str,
    frontier_base_url: str,
    frontier_model: str,
    frontier_kind: str,
    frontier_max_tokens: int,
    selected_case_ids: list[str],
    retry_failures: bool,
    output_dir: Path,
    manifest_path: Path | None = None,
    expert_reference_path: Path = EXPERT_REFERENCE_PATH,
    formal_lock_path: Path | None = None,
    fixture_pack_path: Path | None = None,
    model_selection_run: bool = False,
) -> dict[str, Any]:
    active_manifest_path = manifest_path or (DEVELOPMENT_SET_PATH if dry_run else FORMAL_MANIFEST_PATH)
    pack = _load(active_manifest_path)
    active_fixture_pack_path = fixture_pack_path or (DEVELOPMENT_FIXTURE_PACK_PATH if dry_run else TAXONOMY_PATH)
    fixture_pack = _load(active_fixture_pack_path)
    fixtures = {row["case_id"]: row for row in fixture_pack["cases"]}
    cases = list(pack["cases"])
    if selected_case_ids:
        requested = set(selected_case_ids)
        cases = [row for row in cases if row["case_id"] in requested]
        missing = requested - {row["case_id"] for row in cases}
        if missing:
            raise ValueError(f"unknown_or_non_dry_case_ids:{','.join(sorted(missing))}")
    missing_fixtures = sorted({row["case_id"] for row in cases} - set(fixtures))
    if missing_fixtures:
        raise ValueError(f"fixture_pack_missing_cases:{','.join(missing_fixtures)}")
    expert_reference_accessed = False
    expert_frozen = False
    if model_selection_run:
        if active_manifest_path.resolve() != MODEL_SELECTION_SET_PATH.resolve():
            raise ValueError("model_selection_run_requires_isolated_selection_manifest")
        if active_fixture_pack_path.resolve() != MODEL_SELECTION_FIXTURE_PACK_PATH.resolve():
            raise ValueError("model_selection_run_requires_isolated_selection_fixture_pack")
    if not dry_run:
        expert_reference = _load(expert_reference_path)
        expert_reference_accessed = True
        reference_rows = {row["chart_id"]: row for row in expert_reference.get("references", [])}
        expert_frozen = bool(cases) and all(
            reference_rows.get(row["case_id"], {}).get("status") == "frozen" for row in cases
        )
    if not dry_run and live:
        if formal_lock_path is None:
            raise ValueError("formal_live_run_requires_frozen_formal_lock")
        lock_audit = validate_frozen_formal_lock(
            lock_path=formal_lock_path,
            asset_paths=_formal_lock_asset_paths(),
        )
        if not lock_audit["valid"]:
            raise ValueError(f"formal_lock_invalid:{','.join(lock_audit['errors'])}")
        request_errors = _validate_formal_execution_request(
            lock=lock_audit["lock"],
            active_manifest_path=active_manifest_path,
            expert_reference_path=expert_reference_path,
            selected_lanes=selected_lanes,
            repeats=repeats,
            same_model=same_model,
            frontier_model=frontier_model,
            frontier_kind=frontier_kind,
            frontier_max_tokens=frontier_max_tokens,
        )
        if request_errors:
            raise ValueError(f"formal_request_does_not_match_lock:{','.join(request_errors)}")
        if not expert_frozen:
            raise ValueError("formal_live_run_requires_frozen_expert_references")
        if retry_failures:
            raise ValueError("formal_manual_retry_failures_not_allowed")
    if dry_run and not model_selection_run:
        repeats = 1
    invalid_lanes = sorted(set(selected_lanes) - set(LANES))
    if invalid_lanes:
        raise ValueError(f"unknown_lanes:{','.join(invalid_lanes)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "phase0_checkpoint.jsonl"
    recovered = _load_checkpoint(checkpoint_path)
    rows: list[dict[str, Any]] = []
    run_specs = [
        (case, fixtures[case["case_id"]], lane, repeat)
        for case in cases
        for lane in selected_lanes
        for repeat in range(1, repeats + 1)
    ]
    random.Random(_seed(run_id)).shuffle(run_specs)
    for case_meta, fixture, lane, repeat in run_specs:
        key = f"{case_meta['case_id']}|{lane}|prior|{repeat}"
        if key in recovered and not (retry_failures and recovered[key]["status"] == "failed"):
            rows.append(_refresh_recovered_row(row=recovered[key], fixture=fixture))
            continue
        if not live:
            rows.append(_planned_row(key=key, case_meta=case_meta, fixture=fixture, lane=lane, repeat=repeat))
            continue
        row = _run_lane(
            key=key,
            run_id=run_id,
            case_meta=case_meta,
            fixture=fixture,
            lane=lane,
            repeat=repeat,
            base_url=base_url,
            same_model=same_model,
            frontier_base_url=frontier_base_url,
            frontier_model=frontier_model,
            frontier_kind=frontier_kind,
            frontier_max_tokens=frontier_max_tokens,
        )
        rows.append(row)
        with checkpoint_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(
            json.dumps(
                {
                    "completed": len(rows),
                    "total": len(run_specs),
                    "case_id": case_meta["case_id"],
                    "lane": lane,
                    "status": row["status"],
                    "elapsed_seconds": row.get("elapsed_seconds"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    report = _build_report(
        run_id=run_id,
        dry_run=dry_run,
        live=live,
        repeats=repeats,
        rows=rows,
        cases=cases,
        selected_lanes=selected_lanes,
        same_model=same_model,
        frontier_model=frontier_model,
        frontier_kind=frontier_kind,
        expert_frozen=expert_frozen,
        model_selection_run=model_selection_run,
        resource_access={
            "active_manifest": str(active_manifest_path.relative_to(ROOT)),
            "fixture_pack": str(active_fixture_pack_path.relative_to(ROOT)),
            "full_taxonomy_accessed": active_fixture_pack_path.resolve() == TAXONOMY_PATH.resolve(),
            "formal_manifest_accessed": active_manifest_path.resolve() == FORMAL_MANIFEST_PATH.resolve(),
            "model_selection_manifest_accessed": active_manifest_path.resolve() == MODEL_SELECTION_SET_PATH.resolve(),
            "expert_reference_accessed": expert_reference_accessed,
            "reality_evidence_accessed": False,
        },
    )
    write_report(report=report, output_dir=output_dir)
    return report


def _run_lane(
    *,
    key: str,
    run_id: str,
    case_meta: dict[str, Any],
    fixture: dict[str, Any],
    lane: str,
    repeat: int,
    base_url: str,
    same_model: str,
    frontier_base_url: str,
    frontier_model: str,
    frontier_kind: str,
    frontier_max_tokens: int,
) -> dict[str, Any]:
    world = compile_chart_world(
        reading_id=f"phase0:{run_id}:{case_meta['case_id']}:{repeat}",
        birth_input=_birth(fixture),
        include_research_fixture_prior=False,
    )
    started = time.monotonic()
    model_name = same_model
    try:
        if lane == "direct_same_model":
            reading = _run_direct(
                world=world,
                base_url=base_url,
                model_name=same_model,
                lane_label="direct comparison with chart pillars only",
                include_facts=False,
                direct_power_user=True,
            )
        elif lane == "direct_frontier":
            if not frontier_model:
                raise ValueError("frontier_model_not_configured")
            if frontier_kind != "true_frontier":
                raise ValueError("frontier_policy_not_frozen_as_true_frontier")
            model_name = frontier_model
            reading = _run_direct(
                world=world,
                base_url=frontier_base_url,
                model_name=frontier_model,
                lane_label=f"frontier comparison ({frontier_kind}) with chart pillars only",
                include_facts=False,
                direct_power_user=True,
                max_tokens=frontier_max_tokens,
            )
        elif lane == "fact_only_deepbazi":
            reading = _run_direct(
                world=world,
                base_url=base_url,
                model_name=same_model,
                lane_label="accurate deterministic facts and neutral relations; no ranked tools or reality feedback",
                include_facts=True,
                direct_power_user=True,
            )
        elif lane == "holistic_synthesis":
            reading = _run_direct(
                world=world,
                base_url=base_url,
                model_name=same_model,
                lane_label="trusted facts plus the frozen holistic synthesis protocol; no ranked tools, challenge pack, review, or reality feedback",
                include_facts=True,
                additional_context=_holistic_context_payload(),
            )
        elif lane == "current_v50":
            reading = _run_agent(
                world=world,
                base_url=base_url,
                model_name=same_model,
                compiler=BenchmarkOnlyToolAnchoredCompiler(),
            )
        elif lane == "vnext":
            reading = _run_agent(
                world=world,
                base_url=base_url,
                model_name=same_model,
                compiler=MingliContextCompiler(),
            )
        else:  # pragma: no cover - validated before execution.
            raise ValueError(f"unsupported_lane:{lane}")
        elapsed = round(time.monotonic() - started, 2)
        audit = _audit_reading(reading=reading, world=world, lane=lane, model_name=model_name)
        raw_cognitive_output = reading.model_dump(mode="json")
        raw_cognitive_output_sha256 = sha256(
            json.dumps(raw_cognitive_output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {
            "key": key,
            "case_id": case_meta["case_id"],
            "category": _case_category(case_meta),
            "round": "prior",
            "repeat": repeat,
            "lane": lane,
            "model": model_name,
            "frontier_kind": frontier_kind if lane == "direct_frontier" else "not_applicable",
            "status": "completed",
            "elapsed_seconds": elapsed,
            "pillars": world.pillars,
            # Compatibility alias. New P0 tooling treats raw_cognitive_output as
            # immutable and review_annotations as a separate observation layer.
            "reading": raw_cognitive_output,
            "raw_cognitive_output": raw_cognitive_output,
            "raw_cognitive_output_sha256": raw_cognitive_output_sha256,
            "cognitive_signature": reading.cognitive_signature(),
            "automatic_audit": audit,
            "review_annotations": audit,
        }
    except Exception as exc:  # noqa: BLE001 - a benchmark records failure and does not repair inline.
        return {
            "key": key,
            "case_id": case_meta["case_id"],
            "category": _case_category(case_meta),
            "round": "prior",
            "repeat": repeat,
            "lane": lane,
            "model": model_name,
            "frontier_kind": frontier_kind if lane == "direct_frontier" else "not_applicable",
            "status": "failed",
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "pillars": world.pillars,
            "error": f"{type(exc).__name__}:{exc}",
            "failure_classification": _failure_classification(exc),
        }


def _run_direct(
    *,
    world: Any,
    base_url: str,
    model_name: str,
    lane_label: str,
    include_facts: bool,
    additional_context: dict[str, Any] | None = None,
    max_tokens: int = 4200,
    direct_power_user: bool = False,
) -> CognitiveBenchmarkReading:
    model = OllamaCognitiveModel(
        base_url=base_url,
        model=model_name,
        timeout_seconds=360,
        num_ctx=32768,
    )
    chart_payload = {
        "pillars": world.pillars,
        "gender": world.birth_profile.get("gender", "unknown"),
        "calendar_note": "explicit pillars are authoritative input",
    }
    context_payload: dict[str, Any] = {}
    if include_facts:
        context_payload = {
            "facts": [
                row.model_dump(mode="json")
                for row in world.facts
                if row.authority in {"deterministic_fact", "neutral_relation"}
            ],
            "boundaries": world.boundaries,
        }
    if additional_context:
        context_payload.update(additional_context)
    return model.generate(
        prompt=(
            direct_power_user_prompt(chart_payload=chart_payload)
            + (f"\n\n可信事实与中性关系：\n{context_payload}" if context_payload else "")
            if direct_power_user
            else benchmark_prompt(
                lane_label=lane_label,
                chart_payload=chart_payload,
                context_payload=context_payload,
            )
        ),
        schema=CognitiveBenchmarkReading,
        temperature=0.2,
        thinking=True,
        max_tokens=max_tokens,
    )


def _holistic_context_payload() -> dict[str, Any]:
    policy = _load(HOLISTIC_SYNTHESIS_POLICY_PATH)
    return {
        "holistic_synthesis_protocol": {
            "version": policy["version"],
            "observation_protocol": policy["observation_protocol"],
            "abstract_reasoning_paradigms": policy["abstract_reasoning_paradigms"],
            "forbidden_inputs": policy["forbidden_inputs"],
            "boundaries": policy["boundaries"],
        }
    }


def _run_agent(
    *,
    world: Any,
    base_url: str,
    model_name: str,
    compiler: MingliContextCompiler,
) -> CognitiveBenchmarkReading:
    model = OllamaCognitiveModel(
        base_url=base_url,
        model=model_name,
        timeout_seconds=360,
        num_ctx=32768,
    )
    agent = MingliAgent(
        model=model,
        pattern_model=model,
        work_model=model,
        domain_model=model,
        context_compiler=compiler,
        p0_audit_only=True,
    )
    record = agent.first_reading(case_id=world.reading_id, world=world)
    career = agent.explore_domain(world=world, record=record, domain=LifeDomain.CAREER).reading
    wealth = agent.explore_domain(world=world, record=record, domain=LifeDomain.WEALTH).reading
    return project_cognitive_record(record=record, career=career, wealth=wealth)


def _audit_reading(*, reading: CognitiveBenchmarkReading, world: Any, lane: str, model_name: str) -> dict[str, Any]:
    payload = reading.model_dump(mode="json")
    text = _benchmark_assertive_text(reading)
    conflicts = deterministic_fact_conflicts(text=text, world=world)
    world_model_gaps = [item for item in conflicts if item.startswith("地支关系未建模:")]
    hard_conflicts = [item for item in conflicts if item not in world_model_gaps]
    serialized = json.dumps(payload, ensure_ascii=False)
    leakage = [token for token in (lane, model_name, "expected_contract", "expert_reference") if token and token in serialized]
    allowed_refs = set(world.allowed_evidence_refs)
    unknown_refs = [ref for ref in reading.evidence_refs if allowed_refs and ref not in allowed_refs]
    generic_tokens = [
        token
        for token in ("仅供参考", "机遇与挑战并存", "保持积极", "综合来看", "因人而异")
        if token in serialized
    ]
    return {
        "schema_passed": True,
        "deterministic_fact_conflicts": conflicts,
        "hard_fact_conflicts": hard_conflicts,
        "world_model_gaps": world_model_gaps,
        "lane_or_gold_leakage": leakage,
        "unknown_top_level_evidence_refs": unknown_refs,
        "generic_language_hits": generic_tokens,
        "primary_and_alternative_distinct": (
            reading.primary_hypothesis.name.strip() != reading.strongest_alternative.name.strip()
            and reading.primary_hypothesis.thesis.strip() != reading.strongest_alternative.thesis.strip()
        ),
        "prior_prediction_count": len(reading.prior_predictions),
        "falsifier_count": len(reading.falsifiers),
    }


def _benchmark_assertive_text(reading: CognitiveBenchmarkReading) -> str:
    """Collect asserted benchmark fields without treating alternatives or probes as facts."""

    return "\n".join(
        _unique(
            [
                reading.independent_first_look,
                reading.chart_center_of_gravity,
                reading.primary_hypothesis.name,
                reading.primary_hypothesis.thesis,
                reading.main_work_path,
                reading.body_function_relation,
                *reading.critical_nodes,
                *reading.bridge_or_support_candidates,
                *reading.stable_portrait,
                *reading.career_reasoning.causal_chain,
                *reading.career_reasoning.stable_tendencies,
                *reading.career_reasoning.prior_directions,
                *reading.wealth_reasoning.causal_chain,
                *reading.wealth_reasoning.stable_tendencies,
                *reading.wealth_reasoning.prior_directions,
                *reading.prior_predictions,
            ]
        )
    )


def _build_report(
    *,
    run_id: str,
    dry_run: bool,
    live: bool,
    repeats: int,
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    selected_lanes: list[str],
    same_model: str,
    frontier_model: str,
    frontier_kind: str,
    expert_frozen: bool,
    model_selection_run: bool,
    resource_access: dict[str, Any],
) -> dict[str, Any]:
    completed = [row for row in rows if row["status"] == "completed"]
    failed = [row for row in rows if row["status"] == "failed"]
    planned = [row for row in rows if row["status"] == "planned"]
    model_policy_failures = [
        row for row in failed if row.get("failure_classification") in MODEL_POLICY_FAILURES
    ]
    harness_failures = [row for row in failed if row not in model_policy_failures]
    blind_rows, operator_map = _blind_rows(rows=completed, run_id=run_id)
    pairwise_review_rows = _pairwise_review_rows(blind_rows=blind_rows, operator_map=operator_map)
    harness_integrity_passed = not harness_failures and len(rows) == len(cases) * len(selected_lanes) * repeats
    harness_status = (
        "harness_ready_for_expert_reference_freeze"
        if harness_integrity_passed and live and dry_run
        else "planned"
        if not live
        else "harness_revision_required"
    )
    formal_run_ready = (
        harness_integrity_passed
        and not failed
        and expert_frozen
        and frontier_kind == "true_frontier"
        and bool(frontier_model)
    )
    return {
        "version": "deepbazi.vnext_phase0_cognitive_benchmark_report.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failed else "partial",
        "phase0_decision": harness_status,
        "ready_for_formal_run": formal_run_ready,
        "professional_winner": None,
        "scope": {
            "dry_run": dry_run,
            "live": live,
            "model_selection_run": model_selection_run,
            "rounds": ["prior"],
            "case_count": len(cases),
            "lanes": selected_lanes,
            "repeats": repeats,
            "same_model": same_model,
            "frontier_model": frontier_model,
            "frontier_kind": frontier_kind,
            "true_frontier_comparison_complete": frontier_kind == "true_frontier" and bool(frontier_model),
            "resource_access": resource_access,
        },
        "observed_data": {
            "output_count": len(rows),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "harness_failure_count": len(harness_failures),
            "model_policy_failure_count": len(model_policy_failures),
            "planned_count": len(planned),
            "schema_pass_count": sum(row.get("automatic_audit", {}).get("schema_passed") is True for row in completed),
            "fact_conflict_output_count": sum(bool(row.get("automatic_audit", {}).get("deterministic_fact_conflicts")) for row in completed),
            "hard_fact_conflict_output_count": sum(bool(row.get("automatic_audit", {}).get("hard_fact_conflicts")) for row in completed),
            "world_model_gap_output_count": sum(bool(row.get("automatic_audit", {}).get("world_model_gaps")) for row in completed),
            "lane_leakage_output_count": sum(bool(row.get("automatic_audit", {}).get("lane_or_gold_leakage")) for row in completed),
            "expert_references_frozen": expert_frozen,
            "controlled_feedback_case_count": sum(bool(row.get("controlled_feedback")) for row in cases),
            "failure_classifications": dict(
                Counter(row.get("failure_classification", "unclassified") for row in failed)
            ),
        },
        "lane_results": _lane_summary(rows=rows, selected_lanes=selected_lanes),
        "blind_review_rows": blind_rows,
        "pairwise_review_rows": pairwise_review_rows,
        "operator_map": operator_map,
        "run_rows": rows,
        "interpretation": {
            "observed": f"{len(selected_lanes)} 路输出使用统一合同；preflight 只验证运行、隔离、盲码和可审阅性。",
            "inference": "没有冻结专家参考时，任何自动指标都不能宣布哪条 Lane 命理更好。",
            "recommendation": (
                "完成人类 Expert Reference Freeze、Direct Frontier Policy Freeze、干净代码快照与 FormalRunLock；全部门禁清零前不得运行密封十盘。"
                if harness_status == "harness_ready_for_expert_reference_freeze"
                else "先修复 harness、Lane 路由或盲审隔离，再进入任何冻结步骤。"
            ),
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "ui_modified": False,
            "product_mode_modified": False,
            "shadow_policy_promoted": False,
            "expert_gold_fabricated": False,
            "synthetic_expected_contract_visible_to_model": False,
            "formal_outputs_generated": bool(live and not dry_run and not model_selection_run),
            "sealed_formal_charts_executed": bool(live and not dry_run and not model_selection_run),
            "model_selection_outputs_generated": bool(live and model_selection_run),
            "professional_winner_claimed": False,
            "benchmark_harness_only": True,
            "model_policy_failure_reclassified_as_harness_failure": False,
        },
    }


def _blind_rows(*, rows: list[dict[str, Any]], run_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    packet: list[dict[str, Any]] = []
    mapping: dict[str, Any] = {}
    chart_codes: dict[str, str] = {}
    for row in rows:
        case_id = row["case_id"]
        chart_code = chart_codes.setdefault(case_id, f"CH-{sha256(f'{run_id}|{case_id}'.encode()).hexdigest()[:8].upper()}")
        blind_code = f"BR-{sha256(f'{run_id}|{row['key']}'.encode()).hexdigest()[:12].upper()}"
        lane_group_code = f"LG-{sha256(f'{run_id}|{case_id}|{row['lane']}'.encode()).hexdigest()[:10].upper()}"
        packet.append(
            {
                "blind_code": blind_code,
                "chart_code": chart_code,
                "lane_group_code": lane_group_code,
                "round": row["round"],
                "pillars": row["pillars"],
                "reading": row.get("raw_cognitive_output") or row["reading"],
                "review": _empty_review(),
            }
        )
        mapping[blind_code] = {
            "case_id": case_id,
            "lane": row["lane"],
            "lane_group_code": lane_group_code,
            "model": row["model"],
            "repeat": row["repeat"],
            "round": row["round"],
        }
    random.Random(_seed(f"blind|{run_id}")).shuffle(packet)
    return packet, mapping


def _pairwise_review_rows(
    *,
    blind_rows: list[dict[str, Any]],
    operator_map: dict[str, Any],
) -> list[dict[str, Any]]:
    charts: dict[str, dict[str, list[str]]] = {}
    lanes_by_chart: dict[str, dict[str, str]] = {}
    for row in blind_rows:
        charts.setdefault(row["chart_code"], {}).setdefault(row["lane_group_code"], []).append(row["blind_code"])
        operator = operator_map[row["blind_code"]]
        lanes_by_chart.setdefault(row["chart_code"], {})[operator["lane"]] = row["lane_group_code"]
    return [
        {
            "chart_code": chart_code,
            "anonymous_lane_groups": [
                {
                    "lane_group_code": group_code,
                    "repeat_blind_codes": sorted(codes),
                    "aggregate_strengths": "",
                    "aggregate_failures": "",
                    "resembles_professional_judgment": None,
                }
                for group_code, codes in sorted(groups.items())
            ],
            "ranking": [],
            "required_pairwise_comparisons": [
                {
                    "left_lane_group_code": lanes_by_chart[chart_code][left],
                    "right_lane_group_code": lanes_by_chart[chart_code][right],
                    "preference": None,
                    "reason": "",
                }
                for left, right in CRITICAL_PAIRWISE_LANE_PAIRS
                if left in lanes_by_chart[chart_code] and right in lanes_by_chart[chart_code]
            ],
            "additional_pairwise_preferences": [],
            "adjudication_notes": "",
        }
        for chart_code, groups in sorted(charts.items())
    ]


def _empty_review() -> dict[str, Any]:
    return {
        "salience": None,
        "hypothesis_quality": None,
        "work_path_coherence": None,
        "conditional_roles": None,
        "portrait_specificity": None,
        "career_reasoning": None,
        "wealth_reasoning": None,
        "prior_and_falsifier": None,
        "fact_reliability": None,
        "cross_chart_distinction": None,
        "professional_utility": None,
        "decision": None,
        "notes": "",
    }


def _lane_summary(*, rows: list[dict[str, Any]], selected_lanes: list[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for lane in selected_lanes:
        lane_rows = [row for row in rows if row["lane"] == lane]
        completed = [row for row in lane_rows if row["status"] == "completed"]
        output.append(
            {
                "lane": lane,
                "status": "completed" if len(completed) == len(lane_rows) else "partial",
                "runs": len(lane_rows),
                "completed": len(completed),
                "failures": len([row for row in lane_rows if row["status"] == "failed"]),
                "avg_elapsed_seconds": round(sum(row["elapsed_seconds"] for row in completed) / len(completed), 2) if completed else None,
                "fact_conflict_outputs": sum(bool(row["automatic_audit"]["hard_fact_conflicts"]) for row in completed),
                "world_model_gap_outputs": sum(bool(row["automatic_audit"]["world_model_gaps"]) for row in completed),
                "generic_language_outputs": sum(bool(row["automatic_audit"]["generic_language_hits"]) for row in completed),
            }
        )
    return output


def write_report(*, report: dict[str, Any], output_dir: Path) -> tuple[Path, ...]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "vnext_phase0_benchmark_report_v1.json"
    md_path = output_dir / "vnext_phase0_benchmark_report_v1.md"
    review_path = output_dir / "vnext_phase0_blind_review_packet_v1.md"
    operator_path = output_dir / "vnext_phase0_operator_lane_map_v1.json"
    expert_path = output_dir / "vnext_phase0_expert_reference_freeze_packet_v1.md"
    pairwise_path = output_dir / "vnext_phase0_pairwise_review_packet_v1.md"
    raw_path = output_dir / "vnext_phase0_raw_outputs_v1.jsonl"
    artifact_path = output_dir / "vnext_phase0_artifact_manifest_v1.json"
    public_report = {key: value for key, value in report.items() if key != "operator_map"}
    json_path.write_text(json.dumps(public_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    operator_path.write_text(json.dumps(report["operator_map"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_report_markdown(report), encoding="utf-8")
    review_path.write_text(_review_markdown(report), encoding="utf-8")
    expert_path.write_text(_expert_reference_freeze_markdown(), encoding="utf-8")
    pairwise_path.write_text(_pairwise_review_markdown(report), encoding="utf-8")
    raw_content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in report["run_rows"])
    if raw_path.exists() and raw_path.read_text(encoding="utf-8") != raw_content:
        raise ValueError("immutable_raw_outputs_already_exist_with_different_content")
    if not raw_path.exists():
        raw_path.write_text(raw_content, encoding="utf-8")
    artifacts = {
        "version": "deepbazi.vnext_phase0.artifact_manifest.v1",
        "run_id": report["run_id"],
        "raw_outputs_sha256": sha256(raw_path.read_bytes()).hexdigest(),
        "raw_output_count": len(report["run_rows"]),
        "files": [path.name for path in (json_path, md_path, review_path, pairwise_path, operator_path, expert_path, raw_path)],
    }
    artifact_path.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_path, md_path, review_path, pairwise_path, operator_path, expert_path, raw_path, artifact_path


def _report_markdown(report: dict[str, Any]) -> str:
    observed = report["observed_data"]
    lines = [
        "# VNext Phase 0 Cognitive Benchmark Report v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Phase 0 decision: `{report['phase0_decision']}`",
        f"- Professional winner: `{report['professional_winner']}`",
        f"- Outputs: `{observed['completed_count']}` completed / `{observed['failed_count']}` failed",
        f"- Expert references frozen: `{str(observed['expert_references_frozen']).lower()}`",
        f"- True frontier comparison complete: `{str(report['scope']['true_frontier_comparison_complete']).lower()}`",
        "",
        "## Lane Results",
        "",
        "| Lane | Completed | Failed | Avg seconds | Hard fact conflicts | World-model gaps |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["lane_results"]:
        lines.append(
            f"| {row['lane']} | {row['completed']} | {row['failures']} | {row['avg_elapsed_seconds']} | {row['fact_conflict_outputs']} | {row['world_model_gap_outputs']} |"
        )
    lines.extend(
        [
            "",
            "## Observed Data",
            "",
            "```json",
            json.dumps(observed, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Interpretation",
            "",
            f"- Observed: {report['interpretation']['observed']}",
            f"- Interpretation: {report['interpretation']['inference']}",
            f"- Recommendation: {report['interpretation']['recommendation']}",
            "",
            "## Boundaries",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# VNext Phase 0 Blind Review Packet v1",
        "",
        "本文件不包含 Lane、模型、synthetic case label、expected contract 或专家答案。自动诊断不作为专业评分。",
        "",
    ]
    for row in report["blind_review_rows"]:
        reading = row["reading"]
        lines.extend(
            [
                f"## {row['blind_code']} / {row['chart_code']}",
                "",
                f"- 四柱：`{' · '.join(row['pillars'])}`",
                f"- Round: `{row['round']}`",
                "",
                "### 第一眼与重心",
                "",
                reading["independent_first_look"],
                "",
                reading["chart_center_of_gravity"],
                "",
                "### 主假设 / 最强替代",
                "",
                f"- 主：{reading['primary_hypothesis']['name']} - {reading['primary_hypothesis']['thesis']}",
                f"- 备：{reading['strongest_alternative']['name']} - {reading['strongest_alternative']['thesis']}",
                f"- 比较：{'；'.join(reading['why_primary_over_alternative'])}",
                "",
                "### 做功与体用",
                "",
                reading["main_work_path"],
                "",
                reading["body_function_relation"],
                "",
                "### 事业",
                "",
                "；".join(reading["career_reasoning"]["causal_chain"]),
                "",
                "### 财富",
                "",
                "；".join(reading["wealth_reasoning"]["causal_chain"]),
                "",
                "### 先验 / 可推翻 / Probe",
                "",
                f"- 先验：{'；'.join(reading['prior_predictions'])}",
                f"- 可推翻：{'；'.join(reading['falsifiers'])}",
                f"- Probe：{reading['discriminating_probe']['question']}",
                "",
                "### 人工盲审",
                "",
                "```yaml",
                *[f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in row["review"].items()],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _pairwise_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# VNext Phase 0 Pairwise Lane Review Packet v1",
        "",
        "每个 Lane 以匿名 Group Code 出现，组三次输出需先整体阅读，再做排序与 pairwise preference。",
        "",
    ]
    for row in report["pairwise_review_rows"]:
        lines.extend([f"## {row['chart_code']}", ""])
        for group in row["anonymous_lane_groups"]:
            lines.extend(
                [
                    f"### {group['lane_group_code']}",
                    "",
                    f"- Repeat outputs: `{', '.join(group['repeat_blind_codes'])}`",
                    "- Aggregate strengths:",
                    "- Aggregate failures:",
                    "- Resembles professional Mingli judgment: `null`",
                    "",
                ]
            )
        lines.extend(
            [
                "### Adjudication",
                "",
                "```yaml",
                "ranking: []",
                "pairwise_preferences: []",
                "adjudication_notes: ''",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _expert_reference_freeze_markdown() -> str:
    pack = _load(FORMAL_MANIFEST_PATH)
    taxonomy = _load(TAXONOMY_PATH)
    fixtures = {row["case_id"]: row for row in taxonomy["cases"]}
    lines = [
        "# VNext Phase 0 Expert Reference Freeze Packet v1",
        "",
        "本包只提供四柱与候选分组，不包含 synthetic expected contract、模型输出或自动评分。请保留真实争议，不要求唯一标准答案。",
        "",
        "冻结条件：`must_notice`、可接受主假设、最强替代、关键关系、合理路径、条件性用忌、事业/财富区分、禁止断言与争议均经过专家确认。",
        "",
    ]
    for index, case in enumerate(pack["cases"], start=1):
        birth = fixtures[case["case_id"]]["birth_input"]
        pillars = [birth["year_pillar"], birth["month_pillar"], birth["day_pillar"], birth["hour_pillar"]]
        lines.extend(
            [
                f"## ER-{index:02d}",
                "",
                f"- 四柱：`{' · '.join(pillars)}`",
                f"- 候选分组：`{case['benchmark_role']}`",
                f"- 选择目的：{case['selection_reason']}",
                "",
                "```yaml",
                "status: pending_human_freeze",
                "must_notice: []",
                "acceptable_primary_hypotheses: []",
                "strongest_alternatives: []",
                "unacceptable_or_unsupported_hypotheses: []",
                "critical_relations: []",
                "critical_node_candidates: []",
                "plausible_work_paths: []",
                "blocked_or_failed_paths: []",
                "conditional_useful_roles: []",
                "conditional_harmful_roles: []",
                "unresolved_role_disputes: []",
                "required_domain_distinctions: []",
                "career_prior_expectations: []",
                "wealth_prior_expectations: []",
                "unsupported_claims: []",
                "unresolved_disagreements: []",
                "unresolved_questions: []",
                "author: ''",
                "frozen_at: ''",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _planned_row(*, key: str, case_meta: dict[str, Any], fixture: dict[str, Any], lane: str, repeat: int) -> dict[str, Any]:
    birth = fixture["birth_input"]
    return {
        "key": key,
        "case_id": case_meta["case_id"],
        "category": _case_category(case_meta),
        "round": "prior",
        "repeat": repeat,
        "lane": lane,
        "model": "not_executed",
        "status": "planned",
        "pillars": [birth["year_pillar"], birth["month_pillar"], birth["day_pillar"], birth["hour_pillar"]],
    }


def _unique(values: list[Any]) -> list[str]:
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in output:
            output.append(text)
    return output


def _birth(fixture: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(fixture["birth_input"])
    payload["birth_time"] = "12:00"
    return BirthInputCanonical.model_validate(payload)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_category(case_meta: dict[str, Any]) -> str:
    return str(case_meta.get("category") or case_meta.get("benchmark_role") or "unclassified")


def _formal_lock_asset_paths() -> dict[str, Path]:
    phase0 = ROOT / "data" / "validation" / "phase0"
    return {
        "development_set": DEVELOPMENT_SET_PATH,
        "development_fixture_pack": DEVELOPMENT_FIXTURE_PACK_PATH,
        "model_selection_set": phase0 / "vnext_phase0_model_policy_selection_set_v1.json",
        "formal_manifest": FORMAL_MANIFEST_PATH,
        "expert_reference": EXPERT_REFERENCE_PATH,
        "reality_evidence": REALITY_EVIDENCE_PATH,
        "lane_policy": ROOT / "config" / "vnext_phase0_lane_policy_v1.json",
        "frontier_policy": ROOT / "config" / "vnext_phase0_frontier_policy_v1.json",
        "go_no_go": ROOT / "config" / "vnext_phase0_go_no_go_v1.json",
        "holistic_synthesis_policy": HOLISTIC_SYNTHESIS_POLICY_PATH,
        "modality_policy": ROOT / "config" / "vnext_phase0_modality_policy_v1.json",
        "dependency_lock": ROOT / "config" / "vnext_phase0_dependencies_v1.txt",
        "benchmark_contract": ROOT / "packages" / "core" / "mingli_agent" / "benchmark.py",
        "context_compiler": ROOT / "packages" / "core" / "mingli_agent" / "context.py",
        "cognitive_reasoner": ROOT / "packages" / "core" / "mingli_agent" / "reasoner.py",
        "fact_review": ROOT / "packages" / "core" / "mingli_agent" / "fact_review.py",
        "fact_engine": ROOT / "packages" / "core" / "mingli_agent" / "world.py",
        "benchmark_runner": ROOT / "scripts" / "v50_run_vnext_phase0_benchmark.py",
    }


def _load_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    output: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            output[row["key"]] = row
    return output


def _refresh_recovered_row(*, row: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    if row.get("status") != "completed" or not row.get("reading"):
        return row
    world = compile_chart_world(
        reading_id=f"phase0:recovered:{row['case_id']}:{row['repeat']}",
        birth_input=_birth(fixture),
        include_research_fixture_prior=False,
    )
    raw_cognitive_output = row.get("raw_cognitive_output") or row["reading"]
    reading = CognitiveBenchmarkReading.model_validate(raw_cognitive_output)
    refreshed = dict(row)
    refreshed["raw_cognitive_output"] = raw_cognitive_output
    refreshed["raw_cognitive_output_sha256"] = sha256(
        json.dumps(raw_cognitive_output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    annotations = _audit_reading(
        reading=reading,
        world=world,
        lane=row["lane"],
        model_name=row["model"],
    )
    refreshed["automatic_audit"] = annotations
    refreshed["review_annotations"] = annotations
    return refreshed


def _failure_classification(exc: Exception) -> str:
    text = f"{type(exc).__name__}:{exc}"
    if "model_json_invalid" in text and (text.count("{") > text.count("}") or len(text) > 3000):
        return "schema_output_truncated"
    if "model_json_invalid" in text or "model_json_missing" in text:
        return "schema_failure"
    if "timed out" in text.lower() or "timeout" in text.lower():
        return "model_timeout"
    if "frontier_model_not_configured" in text:
        return "model_not_configured"
    if "frontier_policy_not_frozen" in text:
        return "model_not_configured"
    return "lane_execution_failure"


def _validate_formal_execution_request(
    *,
    lock: dict[str, Any],
    active_manifest_path: Path,
    expert_reference_path: Path,
    selected_lanes: list[str],
    repeats: int,
    same_model: str,
    frontier_model: str,
    frontier_kind: str,
    frontier_max_tokens: int,
) -> list[str]:
    errors: list[str] = []
    if active_manifest_path.resolve() != FORMAL_MANIFEST_PATH.resolve():
        errors.append("formal_manifest_override_not_allowed")
    if expert_reference_path.resolve() != EXPERT_REFERENCE_PATH.resolve():
        errors.append("expert_reference_override_not_allowed")
    if selected_lanes != list(LANES):
        errors.append("formal_lanes_do_not_match_lock")
    execution = lock.get("execution_policy", {})
    if repeats != execution.get("repeats"):
        errors.append("repeat_count_does_not_match_lock")
    same_policy = lock.get("model_policy", {}).get("same_model", {})
    if same_model != same_policy.get("model"):
        errors.append("same_model_does_not_match_lock")
    frontier_policy = lock.get("model_policy", {}).get("frontier") or {}
    if frontier_kind != "true_frontier":
        errors.append("frontier_kind_does_not_match_lock")
    if frontier_model != frontier_policy.get("model"):
        errors.append("frontier_model_does_not_match_lock")
    expected_frontier_budget = frontier_policy.get("token_budget")
    if expected_frontier_budget is not None and frontier_max_tokens != expected_frontier_budget:
        errors.append("frontier_token_budget_does_not_match_lock")
    return errors


def _seed(value: str) -> int:
    return int(sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VNext Phase 0 six-lane cognitive benchmark.")
    parser.add_argument("--run-id", default="phase0-plan")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--lanes", nargs="*", choices=LANES, default=list(LANES))
    parser.add_argument("--base-url", default="http://192.168.0.7:11434")
    parser.add_argument("--same-model", default="qwen3.5:35b")
    parser.add_argument("--frontier-base-url", default="http://192.168.0.7:11434")
    parser.add_argument("--frontier-model", default="")
    parser.add_argument("--frontier-kind", choices=["local_candidate", "true_frontier"], default="true_frontier")
    parser.add_argument("--frontier-max-tokens", type=int, default=6400)
    parser.add_argument("--case-ids", nargs="*", default=[])
    parser.add_argument("--retry-failures", action="store_true")
    parser.add_argument("--manifest-path", default="")
    parser.add_argument("--expert-reference-path", default=str(EXPERT_REFERENCE_PATH))
    parser.add_argument("--formal-lock-path", default="")
    parser.add_argument("--fixture-pack-path", default="")
    parser.add_argument("--model-selection-run", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    report = run_benchmark(
        run_id=args.run_id,
        live=args.live,
        dry_run=args.dry_run,
        repeats=args.repeats,
        selected_lanes=args.lanes,
        base_url=args.base_url,
        same_model=args.same_model,
        frontier_base_url=args.frontier_base_url,
        frontier_model=args.frontier_model,
        frontier_kind=args.frontier_kind,
        frontier_max_tokens=args.frontier_max_tokens,
        selected_case_ids=args.case_ids,
        retry_failures=args.retry_failures,
        output_dir=Path(args.output_dir),
        manifest_path=Path(args.manifest_path) if args.manifest_path else None,
        expert_reference_path=Path(args.expert_reference_path),
        formal_lock_path=Path(args.formal_lock_path) if args.formal_lock_path else None,
        fixture_pack_path=Path(args.fixture_pack_path) if args.fixture_pack_path else None,
        model_selection_run=args.model_selection_run,
    )
    print(json.dumps({"status": report["status"], "decision": report["phase0_decision"]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
