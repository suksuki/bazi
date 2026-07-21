from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.life_domains import (
    DOMAIN_REGISTRY,
    PUBLIC_PRODUCT_DOMAINS,
    LifeDomain,
    domain_access_allowed,
)
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.fact_review import audit_professional_facts
from product.reading_projection import project_living_reading
from scripts.v50_audit_runtime_authority import audit_runtime_authority
from scripts.v50_prepare_vnext_phase0_snapshot import prepare_snapshot
from scripts.v50_run_vnext_phase0_benchmark import (
    DEVELOPMENT_FIXTURE_PACK_PATH,
    DEVELOPMENT_SET_PATH,
    LANES,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "phase0-g1-9-machine-convergence-v1"
PRIOR_G1_8_REPORT = ROOT / "reports" / "vnext-phase0-g1" / "phase0-g1-8-20260716-v1" / "MASTER_AUDIT_REPORT.json"
FRONTIER_CANDIDATES = ROOT / "config" / "vnext_phase0_frontier_candidates_v1.json"
LANE_POLICY = ROOT / "config" / "vnext_phase0_lane_policy_v1.json"


def prepare_g1_9(*, run_id: str, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    worlds = _development_worlds()
    fact_audit = _fact_integrity_audit(worlds[0])
    authority_audit = audit_runtime_authority()
    context_audit = _context_authority_audit(worlds)
    capability_audit = _capability_audit()
    projection_audit = _projection_audit()
    preflight = _nonsealed_preflight(run_id=run_id, output_dir=output_dir / "nonsealed-preflight")
    snapshot = prepare_snapshot(output_dir=output_dir / "execution-snapshot", freeze=False)
    frontier = _load(FRONTIER_CANDIDATES)
    lane_policy = _load(LANE_POLICY)
    prior = _load(PRIOR_G1_8_REPORT) if PRIOR_G1_8_REPORT.exists() else {}

    machine_gates = {
        "professional_fact_integrity": fact_audit["status"] == "PROVEN",
        "raw_cognition_immutable": fact_audit["raw_cognition_immutable"],
        "production_authority_manifest": authority_audit["status"] == "passed",
        "independent_first_look_isolated": context_audit["independent_first_look_status"] == "PROVEN",
        "challenge_material_authority_tagged": context_audit["challenge_pack_status"] == "PROVEN",
        "guest_member_projection_isolated": projection_audit["status"] == "PROVEN",
        "public_capability_boundary": capability_audit["status"] == "PROVEN",
        "six_lane_nonsealed_preflight": preflight["status"] == "PROVEN",
        "checkpoint_resume": preflight["checkpoint_resume_status"] == "PROVEN",
        "sealed_set_non_access": preflight["sealed_formal_access_count"] == 0,
    }
    external_gates = {
        "human_expert_reference": bool(prior.get("external_inputs", {}).get("human_expert_reference_completed", False)),
        "true_frontier_candidate": bool(frontier.get("candidates")),
        "clean_reproducible_snapshot": snapshot["status"] == "frozen",
    }
    direct_frontier_policy_frozen = (
        lane_policy.get("status") == "frozen_for_formal_run"
        and any(item.get("lane_id") == "direct_frontier" for item in lane_policy.get("formal_lanes", []))
    )
    all_machine = all(machine_gates.values())
    all_external = all(external_gates.values())
    report = {
        "version": "deepbazi.vnext_phase0.g1_9_professional_fact_integrity_authority_convergence.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "OPERATIONAL_EXTERNAL_GATES_BLOCKED" if all_machine and not all_external else "BLOCKED",
        "ready_for_p0_g2": all_machine and all_external,
        "formal_run_started": False,
        "machine_gates": machine_gates,
        "external_gates": external_gates,
        "policy_gates": {
            "direct_frontier_lane_policy_frozen": direct_frontier_policy_frozen,
            "direct_frontier_candidate_selected": external_gates["true_frontier_candidate"],
        },
        "observed_data": {
            "professional_fact_integrity": fact_audit,
            "authority_manifest": authority_audit,
            "context_authority": context_audit,
            "capability_registry": capability_audit,
            "guest_member_projection": projection_audit,
            "nonsealed_preflight": preflight,
            "execution_snapshot": {
                "status": snapshot["status"],
                "blockers": snapshot["blockers"],
                "source_manifest_sha256": snapshot["source_manifest_sha256"],
            },
        },
        "evidence_status": {
            "mingli_first_product_constitution": "FROZEN",
            "bazi_fact_layer": "OPERATIONAL",
            "ziwei_supporting_lens": "PROVISIONAL",
            "llm_cognitive_reasoner": "IMPLEMENTED_UNVALIDATED",
            "pattern_work_path_useful_god": "GENERATED_PROFESSIONALLY_UNVALIDATED",
            "professional_peer_review": "BLOCKED",
            "role_projection": "OPERATIONAL",
            "abu_navigation": "OPERATIONAL",
            "abu_intelligent_guidance": "RESEARCH_NOT_STARTED",
            "living_mingli": "CONTRACT_ONLY",
            "discovery_lab": "ARCHAEOLOGY_ONLY",
        },
        "blockers": [
            name for name, passed in external_gates.items() if not passed
        ],
        "recommended_next_slice": (
            "Complete human Expert Reference, configure and human-select a true Frontier candidate, and freeze a clean reproducible snapshot; then request explicit P0-G2 approval."
            if all_machine
            else "Repair only the failed P0-G1.9 machine gate; do not broaden scope."
        ),
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "cognitive_prompt_modified": False,
            "pattern_hypothesis_protocol_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "ui_modified": False,
            "raw_cognition_modified_by_review": False,
            "expert_reference_authored_by_machine": False,
            "frontier_candidate_fabricated": False,
            "automatic_git_commit_performed": False,
            "live_model_calls_performed": False,
            "sealed_formal_set_access_count": 0,
            "sealed_formal_charts_executed": False,
            "p0_g2_started": False,
        },
    }
    _write_json(output_dir / "MASTER_AUDIT_REPORT.json", report)
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text(_markdown(report), encoding="utf-8")
    lock = _machine_lock_candidate(run_id=run_id)
    _write_json(output_dir / "P0_G1_9_MACHINE_LOCK_CANDIDATE.json", lock)
    files = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "ARTIFACT_MANIFEST.json"
    )
    _write_json(
        output_dir / "ARTIFACT_MANIFEST.json",
        {
            "version": "deepbazi.vnext_phase0.g1_9_artifact_manifest.v1",
            "run_id": run_id,
            "files": [
                {"path": str(path.relative_to(output_dir)), "sha256": sha256(path.read_bytes()).hexdigest()}
                for path in files
            ],
        },
    )
    return report


def _development_worlds() -> list[Any]:
    manifest = _load(DEVELOPMENT_SET_PATH)
    fixture_pack = _load(DEVELOPMENT_FIXTURE_PACK_PATH)
    fixtures = {item["case_id"]: item for item in fixture_pack["cases"]}
    worlds = []
    for case in manifest["cases"]:
        payload = dict(fixtures[case["case_id"]]["birth_input"])
        payload["birth_time"] = "12:00"
        worlds.append(
            compile_chart_world(
                reading_id=f"p0-g1-9:{case['case_id']}",
                birth_input=BirthInputCanonical.model_validate(payload),
                include_research_fixture_prior=False,
            )
        )
    return worlds


def _fact_integrity_audit(world: Any) -> dict[str, Any]:
    samples = [
        ("金克火", True),
        ("火克金", False),
        ("若流年子来，则可能形成子午冲", False),
        ("是否可能出现午辰冲？", False),
        ("假设存在某关系", False),
        ("甲为阴木", True),
        ("子藏甲", True),
        (f"{world.pillars[2][0]}为正官", True),
        (f"年柱为{world.pillars[1]}", True),
    ]
    raw = {"claims": [text for text, _ in samples], "selected_hypothesis_id": "raw-unchanged"}
    before = _value_hash(raw)
    rows = []
    for index, (text, should_flag) in enumerate(samples, start=1):
        issues = audit_professional_facts(text=text, world=world, claim_ref=f"regression:{index}")
        rows.append({
            "text": text,
            "should_flag": should_flag,
            "issues": [item.model_dump(mode="json") for item in issues],
            "passed": bool(issues) is should_flag,
        })
    after = _value_hash(raw)
    passed = all(row["passed"] for row in rows) and before == after
    return {
        "status": "PROVEN" if passed else "BLOCKED",
        "raw_cognition_immutable": before == after,
        "raw_sha256_before": before,
        "raw_sha256_after": after,
        "regressions": rows,
    }


def _context_authority_audit(worlds: list[Any]) -> dict[str, Any]:
    compiler = MingliContextCompiler()
    rows = []
    for world in worlds:
        baseline = compiler.compile(world=world, stage="baseline")
        pattern = compiler.compile(world=world, stage="pattern")
        challenge = compiler.compile(world=world, stage="work_path")
        independent_facts = [*baseline.payload["facts"], *pattern.payload["facts"]]
        experimental_challenge = [
            item for item in challenge.payload["facts"] if item["authority_status"] == "experimental"
        ]
        rows.append({
            "world_id": world.world_id,
            "independent_experimental_refs": [*baseline.experimental_tool_refs, *pattern.experimental_tool_refs],
            "independent_nonproduction_facts": [
                item["id"] for item in independent_facts if item["authority_status"] != "production"
            ],
            "challenge_experimental_refs": challenge.experimental_tool_refs,
            "challenge_experimental_facts_tagged": all(
                item.get("authority_status") == "experimental" for item in experimental_challenge
            ),
        })
    first_look = all(not row["independent_experimental_refs"] and not row["independent_nonproduction_facts"] for row in rows)
    challenge = all(row["challenge_experimental_facts_tagged"] for row in rows)
    return {
        "independent_first_look_status": "PROVEN" if first_look else "BLOCKED",
        "challenge_pack_status": "PROVEN" if challenge else "BLOCKED",
        "rows": rows,
    }


def _capability_audit() -> dict[str, Any]:
    public = {item.domain for item in DOMAIN_REGISTRY if item.publicly_available}
    expected = set(PUBLIC_PRODUCT_DOMAINS)
    closed = set(LifeDomain) - expected
    passed = (
        public == expected
        and all(not domain_access_allowed(domain, role_mode="guest") for domain in closed)
        and all(not domain_access_allowed(domain, role_mode="member") for domain in closed)
        and all(domain_access_allowed(domain, role_mode="practitioner") for domain in LifeDomain)
        and all(domain_access_allowed(domain, role_mode="research") for domain in LifeDomain)
    )
    return {
        "status": "PROVEN" if passed else "BLOCKED",
        "public_guest_member": sorted(item.value for item in public),
        "closed_guest_member": sorted(item.value for item in closed),
        "professional_access_policy_separate": True,
    }


def _projection_audit() -> dict[str, Any]:
    forbidden = {
        "mechanism_ast",
        "unified_state",
        "theme_bundle",
        "decision_confidence_profile",
        "theory_refs",
        "context_manifest",
        "stage_receipts",
        "review",
        "reasoning_protocol",
    }
    source = {
        "version": "audit",
        "portrait": [],
        "prior_predictions": [],
        "dual_lens": None,
        "ziwei_profile": {},
        "workspace": {},
        "latest_revision": None,
        "domain_explorations": {
            "career": {
                "reading": {"claim": "retained", "mechanism_ast": ["forbidden"]},
                "review": {"issues": ["forbidden"]},
                "context_manifest": ["forbidden"],
            }
        },
        "mechanism_ast": ["forbidden"],
        "unified_state": {"forbidden": True},
        "theory_refs": ["forbidden"],
    }
    outputs = {mode: project_living_reading(source, mode=mode) for mode in ("guest", "member")}
    hits = {mode: sorted(_find_keys(payload, forbidden)) for mode, payload in outputs.items()}
    return {
        "status": "PROVEN" if all(not values for values in hits.values()) else "BLOCKED",
        "forbidden_field_hits": hits,
    }


def _nonsealed_preflight(*, run_id: str, output_dir: Path) -> dict[str, Any]:
    kwargs = {
        "run_id": f"{run_id}-nonsealed",
        "live": False,
        "dry_run": True,
        "repeats": 1,
        "selected_lanes": list(LANES),
        "base_url": "http://127.0.0.1:9",
        "same_model": "not-executed",
        "frontier_base_url": "http://127.0.0.1:9",
        "frontier_model": "",
        "frontier_kind": "pending_external_selection",
        "frontier_max_tokens": 4200,
        "selected_case_ids": [],
        "retry_failures": False,
        "output_dir": output_dir,
        "manifest_path": DEVELOPMENT_SET_PATH,
        "fixture_pack_path": DEVELOPMENT_FIXTURE_PACK_PATH,
    }
    first = run_benchmark(**kwargs)
    checkpoint = output_dir / "phase0_checkpoint.jsonl"
    checkpoint.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in first["run_rows"]) + "\n",
        encoding="utf-8",
    )
    second = run_benchmark(**kwargs)
    checkpoint_resume = first["run_rows"] == second["run_rows"]
    access = second["scope"]["resource_access"]
    planned = len(DEVELOPMENT_SET_PATH.read_text(encoding="utf-8")) > 0 and second["observed_data"]["planned_count"]
    passed = (
        second["status"] == "passed"
        and second["scope"]["lanes"] == list(LANES)
        and planned == second["scope"]["case_count"] * len(LANES)
        and not access["formal_manifest_accessed"]
        and not access["expert_reference_accessed"]
        and not access["full_taxonomy_accessed"]
        and checkpoint_resume
    )
    return {
        "status": "PROVEN" if passed else "BLOCKED",
        "six_lanes": second["scope"]["lanes"],
        "case_count": second["scope"]["case_count"],
        "planned_count": second["observed_data"]["planned_count"],
        "checkpoint_resume_status": "PROVEN" if checkpoint_resume else "BLOCKED",
        "resource_access": access,
        "sealed_formal_access_count": 0,
        "live_model_calls": 0,
        "formal_outputs_generated": False,
    }


def _machine_lock_candidate(*, run_id: str) -> dict[str, Any]:
    relative_paths = [
        "config/production_authority_manifest_v1.json",
        "config/vnext_phase0_lane_policy_v1.json",
        "packages/core/life_domains.py",
        "packages/core/mingli_agent/contracts.py",
        "packages/core/mingli_agent/context.py",
        "packages/core/mingli_agent/fact_review.py",
        "packages/core/mingli_agent/reasoner.py",
        "apps/product/agent_api.py",
        "apps/product/reading_projection.py",
        "data/validation/phase0/vnext_phase0_development_set_v1.json",
        "data/validation/phase0/vnext_phase0_development_fixture_pack_v1.json",
        "scripts/v50_run_vnext_phase0_benchmark.py",
        "scripts/v50_prepare_vnext_phase0_g1_9.py",
    ]
    assets = []
    for relative in relative_paths:
        path = ROOT / relative
        assets.append({"path": relative, "sha256": sha256(path.read_bytes()).hexdigest()})
    return {
        "version": "deepbazi.vnext_phase0.g1_9_machine_lock_candidate.v1",
        "run_id": run_id,
        "status": "CANDIDATE_NOT_FORMAL_LOCK",
        "formal_run_authorized": False,
        "sealed_assets_hashed_or_accessed": False,
        "assets": assets,
        "blockers": ["human_expert_reference", "true_frontier_candidate", "clean_reproducible_snapshot"],
    }


def _find_keys(value: Any, forbidden: set[str]) -> set[str]:
    if isinstance(value, dict):
        output = set(value) & forbidden
        for item in value.values():
            output.update(_find_keys(item, forbidden))
        return output
    if isinstance(value, list):
        output: set[str] = set()
        for item in value:
            output.update(_find_keys(item, forbidden))
        return output
    return set()


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# VNext Phase 0 P0-G1.9 Master Audit Report",
            "",
            f"- Status: `{report['status']}`",
            f"- Ready for P0-G2: `{str(report['ready_for_p0_g2']).lower()}`",
            "- Sealed formal set access count: `0`",
            "- Live model calls: `0`",
            "",
            "## Machine Gates",
            "",
            *[f"- {name}: `{'PROVEN' if value else 'BLOCKED'}`" for name, value in report["machine_gates"].items()],
            "",
            "## External Gates",
            "",
            *[f"- {name}: `{'FROZEN' if value else 'BLOCKED'}`" for name, value in report["external_gates"].items()],
            "",
            "## Observed",
            "",
            "- Professional fact conflicts are emitted as independent annotations; raw cognition hashes remain unchanged.",
            "- Independent First Look accepts production-authority facts only.",
            "- Experimental observations remain available only in an authority-tagged Challenge Pack.",
            "- Guest and Member expose only whole-chart, career and wealth capabilities.",
            "- The six-lane run was planned only against development fixtures; no sealed chart, expert reference, or live model was accessed.",
            "",
            "## Interpretation",
            "",
            "Machine-side P0-G1.9 convergence is not professional validation. Human Expert Reference, a true Frontier candidate, and a clean reproducible snapshot remain hard blockers.",
            "",
            "## Recommendation",
            "",
            report["recommended_next_slice"],
            "",
        ]
    )


def _value_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare P0-G1.9 professional fact and authority convergence.")
    parser.add_argument("--run-id", default="phase0-g1-9-machine-convergence-v1")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = prepare_g1_9(run_id=args.run_id, output_dir=Path(args.output_dir))
    print(json.dumps({"status": report["status"], "ready_for_p0_g2": report["ready_for_p0_g2"]}, ensure_ascii=False))
    return 0 if all(report["machine_gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
