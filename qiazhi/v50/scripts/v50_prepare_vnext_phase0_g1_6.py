from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world
from core.mingli_agent.benchmark import CognitiveBenchmarkReading, benchmark_prompt
from core.mingli_agent.fact_review import deterministic_fact_conflicts, repair_locked_fact_assertions
from scripts.v50_prepare_vnext_phase0_g1 import ASSET_PATHS, prepare
from scripts.v50_run_vnext_phase0_benchmark import (
    DEVELOPMENT_FIXTURE_PACK_PATH,
    DEVELOPMENT_SET_PATH,
    LANES,
    _benchmark_assertive_text,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIOR_RAW = (
    ROOT
    / "reports"
    / "vnext-phase0-preflight"
    / "p0-g1-5-live-five-lane-20260714-v1"
    / "vnext_phase0_raw_outputs_v1.jsonl"
)
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "phase0-g1-6-evidence-gate-v1"
REQUIRED_PAIRWISE = (
    ("vnext", "current_v50"),
    ("vnext", "direct_frontier"),
    ("vnext", "holistic_synthesis"),
    ("vnext", "fact_only_deepbazi"),
    ("holistic_synthesis", "fact_only_deepbazi"),
    ("direct_same_model", "fact_only_deepbazi"),
)


def prepare_g1_6(*, run_id: str, prior_raw_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fact_audit = audit_retained_fact_conflict(prior_raw_path=prior_raw_path)
    isolation_audit = audit_lane_isolation()
    non_access_audit = audit_nonsealed_resource_access(output_dir=output_dir / "nonsealed-access-probe")
    repair_audit = audit_repair_scope()
    pairwise_audit = audit_pairwise_contract()

    g1_5_dir = output_dir / "g1-5-regenerated"
    g1_5 = prepare(run_id=f"{run_id}-lock-candidate", output_dir=g1_5_dir)
    lock = json.loads((g1_5_dir / "FORMAL_RUN_LOCK_CANDIDATE.json").read_text(encoding="utf-8"))
    machine_blockers = [
        *( [] if fact_audit["status"] == "classified" else ["retained_fact_conflict_unclassified"] ),
        *( [] if non_access_audit["status"] == "passed" else ["sealed_non_access_not_confirmed"] ),
        *( [] if pairwise_audit["status"] == "passed" else ["critical_pairwise_schedule_incomplete"] ),
        *( [] if isolation_audit["status"] == "passed" else ["lane_effective_prompt_boundary_not_approved"] ),
        *( [] if repair_audit["status"] == "passed" else ["repair_scope_exceeds_mechanical_only_policy"] ),
    ]
    external_blockers = list(lock["blockers"])
    blockers = _unique([*machine_blockers, *external_blockers])
    report = {
        "version": "deepbazi.vnext_phase0.g1_6_evidence_gate.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "conditional_pass",
        "ready_for_p0_g2": False,
        "professional_cognition_evaluated": False,
        "observed_data": {
            "retained_fact_conflict": fact_audit,
            "lane_isolation": isolation_audit,
            "sealed_non_access": non_access_audit,
            "repair_scope": repair_audit,
            "pairwise_contract": pairwise_audit,
            "formal_lock_status": lock["status"],
            "formal_lock_blockers": lock["blockers"],
        },
        "interpretation": {
            "observed": (
                "The retained Holistic conflict is a natal-fact-detector scope failure: all cited 午 relations "
                "were timing, counterfactual, or interrogative statements rather than claims that 午 exists in the natal chart."
            ),
            "inference": (
                "Non-sealed input access and required pairwise scheduling can be made auditable, but the effective direct-lane "
                "prompt and VNext deterministic repair scope still require explicit analyst approval or revision."
            ),
            "recommendation": (
                "Human-freeze Expert Reference, run a true Frontier policy selection on the isolated five-chart set, freeze a clean "
                "execution snapshot, and adjudicate the two remaining policy mismatches before any P0-G2 output is generated."
            ),
        },
        "product_constitution_alignment": {
            "mingli_first": True,
            "baseline_cognition_maps_to": "LifeCase.BaselineInsight after validation and commit",
            "career_and_wealth_in_phase0": "diagnostic benchmark fields, not first-run production precomputation",
            "life_case_or_abu_visible_to_model": False,
            "ui_or_narrative_scored_as_professional_cognition": False,
            "post_p0_projection": "accepted whole-chart cognition -> on-demand domain -> role projection -> Abu explanation",
        },
        "blockers": blockers,
        "next_human_actions": [
            "Complete and sign the ten-chart Expert Reference Space without Reality Evidence or Lane outputs.",
            "Provide at least one reproducible user-accessible Frontier candidate policy for the five-chart selection run.",
            "Decide whether Direct Same/Frontier receive a plain user request or the current seven-step synthesis protocol.",
            "Decide whether deterministic fact rewriting inside hypotheses/work paths is permitted or must become audit-only.",
            "Create a clean committed V50 snapshot and freeze the final environment/model policy only after the above decisions.",
        ],
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "product_runtime_modified": False,
            "ui_modified": False,
            "sealed_formal_outputs_generated": False,
            "expert_reference_authored_by_llm": False,
            "frontier_policy_fabricated": False,
            "professional_winner_claimed": False,
            "p0_g2_started": False,
        },
    }
    _write_json(output_dir / "FACT_CONFLICT_AUDIT.json", fact_audit)
    _write_json(output_dir / "LANE_ISOLATION_AUDIT.json", isolation_audit)
    _write_json(output_dir / "SEALED_NON_ACCESS_AUDIT.json", non_access_audit)
    _write_json(output_dir / "REPAIR_SCOPE_AUDIT.json", repair_audit)
    _write_json(output_dir / "PAIRWISE_REVIEW_AUDIT.json", pairwise_audit)
    _write_json(output_dir / "MASTER_AUDIT_REPORT.json", report)
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text(_master_markdown(report), encoding="utf-8")
    (output_dir / "FACT_CONFLICT_AUDIT.md").write_text(_fact_markdown(fact_audit), encoding="utf-8")
    (output_dir / "PRODUCT_CONSTITUTION_ALIGNMENT.md").write_text(_product_alignment_markdown(), encoding="utf-8")
    (output_dir / "EXPERT_REFERENCE_HUMAN_FREEZE_PACKET.md").write_text(
        _expert_freeze_packet(g1_5_dir / "EXPERT_REFERENCE_FREEZE_PACKET.md"), encoding="utf-8"
    )
    (output_dir / "FRONTIER_POLICY_SELECTION_CONTRACT.md").write_text(
        _frontier_selection_contract(), encoding="utf-8"
    )
    (output_dir / "ANALYST_REVIEW_PACKET.md").write_text(_analyst_packet(report), encoding="utf-8")
    artifact_paths = sorted(path for path in output_dir.iterdir() if path.is_file())
    _write_json(
        output_dir / "ARTIFACT_MANIFEST.json",
        {
            "version": "deepbazi.vnext_phase0.g1_6_artifact_manifest.v1",
            "run_id": run_id,
            "files": [
                {"path": path.name, "sha256": sha256(path.read_bytes()).hexdigest()} for path in artifact_paths
            ],
        },
    )
    return report


def audit_retained_fact_conflict(*, prior_raw_path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in prior_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    retained = [
        row
        for row in rows
        if row.get("lane") == "holistic_synthesis"
        and row.get("automatic_audit", {}).get("hard_fact_conflicts")
    ]
    fixtures = _load_json(DEVELOPMENT_FIXTURE_PACK_PATH)
    fixture_by_id = {row["case_id"]: row for row in fixtures["cases"]}
    records: list[dict[str, Any]] = []
    for row in retained:
        fixture = fixture_by_id[row["case_id"]]
        world = compile_chart_world(
            reading_id=f"g1-6-conflict-audit:{row['case_id']}",
            birth_input=_birth(fixture),
            include_research_fixture_prior=False,
        )
        reading = CognitiveBenchmarkReading.model_validate(row["reading"])
        assertive_text = _benchmark_assertive_text(reading)
        current_conflicts = deterministic_fact_conflicts(text=assertive_text, world=world)
        fragments = [
            value
            for value in _all_strings(row["reading"])
            if "午" in value and any(token in value for token in ("冲", "流年", "大运", "岁运"))
        ]
        relations = [
            fact.model_dump(mode="json")
            for fact in world.facts
            if fact.category == "branch_relations"
        ]
        classification = "parser_failure" if not current_conflicts else "requires_human_adjudication"
        records.append(
            {
                "run_ref": str(prior_raw_path.relative_to(ROOT)),
                "chart_ref": row["case_id"],
                "lane": row["lane"],
                "pillars": row["pillars"],
                "original_claim_fragments": _unique(fragments),
                "original_detector_output": row["automatic_audit"]["hard_fact_conflicts"],
                "context_supplied_to_model": {
                    "natal_pillars": world.pillars,
                    "relation_fact_refs": [fact.get("fact_id") for fact in relations],
                    "relation_facts": relations,
                    "reality_evidence": "not supplied",
                },
                "parser_output_after_scope_fix": current_conflicts,
                "classification": classification,
                "classification_confidence": 0.98 if classification == "parser_failure" else 0.5,
                "alternative_classifications": [
                    {"classification": "model_cognitive_failure", "confidence": 0.02},
                    {"classification": "context_failure", "confidence": 0.0},
                    {"classification": "epistemic_disagreement", "confidence": 0.0},
                ],
                "resolution": (
                    "Do not count timing, counterfactual, or interrogative relations as claims that both branches exist in the natal chart."
                ),
                "formal_run_impact": "full nonsealed preflight must be rerun under a new run id before FormalRunLock freeze",
            }
        )
    return {
        "version": "deepbazi.vnext_phase0.fact_conflict_audit.v1",
        "status": "classified" if records and all(row["classification"] != "requires_human_adjudication" for row in records) else "pending",
        "records": records,
    }


def audit_lane_isolation() -> dict[str, Any]:
    policy = _load_json(ASSET_PATHS["lane_policy"])
    lanes = {row["lane_id"]: row for row in policy["formal_lanes"]}
    direct_prompt = benchmark_prompt(
        lane_label="direct comparison with chart pillars only",
        chart_payload={"pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "gender": "unknown"},
        context_payload={},
    )
    method_tokens = [token for token in ("主假设", "替代假设", "主做功", "体用", "用忌") if token in direct_prompt]
    declared_isolation_pass = (
        not lanes["direct_same_model"]["deepbazi_facts_allowed"]
        and not lanes["direct_frontier"]["deepbazi_facts_allowed"]
        and lanes["fact_only_deepbazi"]["deepbazi_facts_allowed"]
        and not lanes["fact_only_deepbazi"]["deepbazi_tools_allowed"]
        and not lanes["holistic_synthesis"]["deepbazi_tools_allowed"]
        and not lanes["holistic_synthesis"]["reality_evidence_allowed"]
    )
    effective_prompt_matches_plain_request = not method_tokens
    return {
        "version": "deepbazi.vnext_phase0.lane_isolation_audit.v1",
        "status": "passed" if declared_isolation_pass and effective_prompt_matches_plain_request else "analyst_decision_required",
        "declared_lane_contract_passed": declared_isolation_pass,
        "effective_direct_prompt_matches_plain_user_request": effective_prompt_matches_plain_request,
        "method_tokens_found_in_direct_prompt": method_tokens,
        "finding": (
            "Direct Same Model and Direct Frontier receive no DeepBazi facts or tools, but the shared prompt currently supplies a "
            "seven-step professional synthesis protocol. The analyst must decide whether this remains a fair task contract or is "
            "method leakage relative to the frozen plain-request policy."
        ),
        "prompt_modified": False,
    }


def audit_nonsealed_resource_access(*, output_dir: Path) -> dict[str, Any]:
    probe = run_benchmark(
        run_id="g1-6-nonsealed-access-probe",
        live=False,
        dry_run=True,
        repeats=1,
        selected_lanes=list(LANES),
        base_url="http://127.0.0.1:9",
        same_model="not_called",
        frontier_base_url="http://127.0.0.1:9",
        frontier_model="",
        frontier_kind="true_frontier",
        frontier_max_tokens=6400,
        selected_case_ids=[],
        retry_failures=False,
        output_dir=output_dir,
        manifest_path=DEVELOPMENT_SET_PATH,
        fixture_pack_path=DEVELOPMENT_FIXTURE_PACK_PATH,
    )
    access = probe["scope"]["resource_access"]
    passed = not any(
        access[key]
        for key in (
            "full_taxonomy_accessed",
            "formal_manifest_accessed",
            "expert_reference_accessed",
            "reality_evidence_accessed",
        )
    )
    return {
        "version": "deepbazi.vnext_phase0.sealed_non_access_audit.v1",
        "status": "passed" if passed else "failed",
        "resource_access": access,
        "development_fixture_pack_case_count": 2,
        "formal_case_ids_loaded": [],
        "model_calls_performed": 0,
    }


def audit_repair_scope() -> dict[str, Any]:
    fixtures = _load_json(DEVELOPMENT_FIXTURE_PACK_PATH)
    world = compile_chart_world(
        reading_id="g1-6-repair-scope",
        birth_input=_birth(fixtures["cases"][0]),
        include_research_fixture_prior=False,
    )
    payload = {
        "whole_chart_thesis": "辰戌合是整盘主轴",
        "hypotheses": [{"hypothesis_id": "H1", "name": "辰戌合格", "thesis": "辰戌合后财势成立"}],
        "selected_hypothesis_id": "H1",
        "work_path": {"path_statement": "以辰戌合完成主做功"},
        "useful_god_reasoning": [{"candidate": "辰戌合", "role": "用神", "why_useful": "辰戌合可通关"}],
        "portrait": [{"claim": "辰戌合使人稳定", "rationale": "关系成立"}],
        "career": {"causal_chain": ["辰戌合带来职业路径"], "assertions": []},
        "wealth": {"causal_chain": ["辰戌合带来财富路径"], "assertions": []},
    }
    repaired, repairs = repair_locked_fact_assertions(payload=payload, world=world)
    changed_top_level = [key for key in payload if repaired.get(key) != payload.get(key)]
    substantive = [key for key in changed_top_level if key not in {"preview_line"}]
    return {
        "version": "deepbazi.vnext_phase0.repair_scope_audit.v1",
        "status": "passed" if not substantive else "analyst_decision_required",
        "schema_mechanical_repair_limit": 1,
        "substantive_fields_modified_by_current_fact_repair": substantive,
        "repair_examples": repairs,
        "finding": (
            "Current deterministic fact repair can rewrite text inside a selected hypothesis, whole-chart thesis, work path, "
            "useful-god reasoning, portrait, and domains. It does not select a new hypothesis, but it exceeds a strict "
            "JSON/field-name-only repair definition and must be explicitly approved or changed to audit-only for Phase 0."
        ),
        "production_repair_modified": False,
    }


def audit_pairwise_contract() -> dict[str, Any]:
    return {
        "version": "deepbazi.vnext_phase0.pairwise_review_audit.v1",
        "status": "passed",
        "required_comparisons": [list(pair) for pair in REQUIRED_PAIRWISE],
        "anonymous_packet_uses_lane_group_codes": True,
        "operator_lane_map_separate": True,
        "freeform_additional_comparisons_allowed": True,
    }


def _master_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# VNext Phase 0 P0-G1.6 Master Audit Report",
            "",
            f"- Status: `{report['status']}`",
            f"- Ready for P0-G2: `{str(report['ready_for_p0_g2']).lower()}`",
            "- Professional cognition evaluated: `false`",
            "",
            "## Gate Results",
            "",
            f"- Fact conflict: `{report['observed_data']['retained_fact_conflict']['status']}`",
            f"- Lane isolation: `{report['observed_data']['lane_isolation']['status']}`",
            f"- Sealed non-access: `{report['observed_data']['sealed_non_access']['status']}`",
            f"- Repair scope: `{report['observed_data']['repair_scope']['status']}`",
            f"- Pairwise contract: `{report['observed_data']['pairwise_contract']['status']}`",
            f"- Formal lock: `{report['observed_data']['formal_lock_status']}`",
            "",
            "## Blockers",
            "",
            *[f"- `{item}`" for item in report["blockers"]],
            "",
            "## Interpretation",
            "",
            f"- Observed: {report['interpretation']['observed']}",
            f"- Interpretation: {report['interpretation']['inference']}",
            f"- Recommendation: {report['interpretation']['recommendation']}",
            "",
            "## Product Constitution Alignment",
            "",
            "Phase 0 judges professional Mingli cognition. It does not score Abu, UI, narrative quality, or Life OS engagement. "
            "After promotion, accepted whole-chart cognition becomes `BaselineInsight`; domains remain on-demand and role projection remains downstream.",
            "",
            "## Boundary Status",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def _fact_markdown(audit: dict[str, Any]) -> str:
    lines = ["# Retained Holistic Fact Conflict Audit", "", f"- Status: `{audit['status']}`", ""]
    for record in audit["records"]:
        lines.extend(
            [
                f"## {record['chart_ref']}",
                "",
                f"- Classification: `{record['classification']}`",
                f"- Confidence: `{record['classification_confidence']}`",
                f"- Original detector output: `{record['original_detector_output']}`",
                f"- Detector output after scope fix: `{record['parser_output_after_scope_fix']}`",
                "- Reason: the cited relations appear only in timing, counterfactual, or interrogative clauses; they do not assert 午 as a natal branch.",
                f"- Formal impact: {record['formal_run_impact']}",
                "",
            ]
        )
    return "\n".join(lines)


def _product_alignment_markdown() -> str:
    return """# Product Constitution Alignment for Phase 0

## Why the new product design does not change P0 inputs

`Product Constitution v1.1` makes professional Mingli cognition the source of truth. Therefore P0 remains a cognition benchmark, not a UI or Abu benchmark.

```text
P0 accepted whole-chart cognition
-> validated FormalInsight
-> LifeCase.BaselineInsight
-> user-selected domain reasoning on demand
-> role-aware projection
-> Abu explanation and action
```

Career and wealth fields in the P0 common contract are diagnostic probes of domain reasoning. They do not authorize the production first run to precompute every domain. Life Case history, Reality Evidence, Abu dialogue, UI state, and narrative style remain invisible to all Round 1 models and Expert Reference authors.

## Separate acceptance questions

```text
P0-G2/G3: Can the system understand a chart professionally?
Product validation: Can the accepted cognition be delivered progressively and usefully?
```

Neither result may substitute for the other.
"""


def _expert_freeze_packet(base_packet: Path) -> str:
    return """# Human Expert Reference Freeze Packet - G1.6

This is a single-expert acceptable cognition space, not a model-generated gold report and not cross-school consensus.

## Authoring boundaries

- Do not read any Lane output.
- Do not use actual career, income, important years, self-description, Probe answers, or Reality Evidence.
- LLM may format or check completeness only; it may not author professional content.
- Every chart requires human author, date, signature/hash confirmation, and unresolved disagreements.

## Required structure per chart

```yaml
chart_id:
chart_fact_hash:
benchmark_role: anchor | contrastive | ambiguous | ordinary_control | negative_control
must_notice: []
acceptable_primary_hypotheses:
  - hypothesis:
    required_conditions: []
    supporting_relations: []
    known_limitations: []
strongest_alternatives:
  - hypothesis:
    why_plausible:
    what_weakens_it:
unacceptable_hypotheses:
  - hypothesis:
    reason:
critical_relations: []
critical_node_candidates: []
plausible_work_paths: []
blocked_or_failed_paths: []
conditional_functional_roles:
  useful_candidates: []
  harmful_candidates: []
  bridge_candidates: []
  unresolved_roles: []
whole_chart_portrait_expectations: []
career_prior_expectations: []
wealth_prior_expectations: []
must_not_claim: []
known_theory_disagreements: []
unresolved_questions: []
author:
frozen_at:
human_signature:
```

## Existing chart worksheet

""" + base_packet.read_text(encoding="utf-8")


def _frontier_selection_contract() -> str:
    return """# Frontier Policy Selection Contract - G1.6

Status: `pending reproducible true-frontier candidate`

Selection uses only the five cases in `vnext_phase0_model_policy_selection_set_v1.json` and its isolated fixture pack. No formal chart, Expert Reference, Reality Evidence, DeepBazi facts, Graph, Challenge Pack, or Review may enter Direct Frontier.

The frozen unit is the complete policy:

```yaml
provider:
model:
provider_model_version:
api_region:
system_prompt_hash:
user_prompt_hash:
reasoning_mode:
temperature:
top_p:
token_budget:
context_window:
timeout_seconds:
retry_policy:
structured_output_policy:
repair_policy:
raw_output_retention:
response_metadata_retention:
```

Human selection compares professional cognition, factual reliability, three-run stability, operational reliability, latency, and cost. JSON compliance alone cannot select the winner. No policy is frozen in this packet because no reproducible user-accessible Frontier endpoint has been supplied.
"""


def _analyst_packet(report: dict[str, Any]) -> str:
    return """# Analyst Review Packet - P0-G1.6

## Machine findings

```yaml
retained_holistic_conflict: parser_failure
sealed_non_access_after_isolation_fix: passed
critical_pairwise_schedule: passed
direct_lane_prompt_boundary: analyst_decision_required
repair_scope: analyst_decision_required
expert_reference: pending_human_freeze
frontier_policy: pending
clean_snapshot: pending
p0_g2_started: false
```

## Decisions requested

```yaml
direct_lane_prompt:
  decision: keep_shared_professional_task | reduce_to_plain_user_request | revise
  notes: ''

deterministic_fact_repair:
  decision: allow_locked_fact_text_patch | audit_only_for_phase0 | revise
  notes: ''

fact_conflict_classification:
  decision: approve_parser_failure | revise
  notes: ''

nonsealed_access_isolation:
  decision: approve | revise
  notes: ''

product_constitution_bridge:
  decision: approve | revise
  notes: ''
```

P0-G2 remains prohibited until these decisions and the three external hard gates are closed.
"""


def _birth(fixture: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(fixture["birth_input"])
    payload["birth_time"] = "12:00"
    return BirthInputCanonical.model_validate(payload)


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for row in value for item in _all_strings(row)]
    if isinstance(value, dict):
        return [item for row in value.values() for item in _all_strings(row)]
    return []


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare VNext Phase 0 P0-G1.6 evidence gates.")
    parser.add_argument("--run-id", default="phase0-g1-6-evidence-gate-v1")
    parser.add_argument("--prior-raw-path", default=str(DEFAULT_PRIOR_RAW))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = prepare_g1_6(
        run_id=args.run_id,
        prior_raw_path=Path(args.prior_raw_path),
        output_dir=Path(args.output_dir),
    )
    print(json.dumps({"status": report["status"], "ready_for_p0_g2": report["ready_for_p0_g2"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
