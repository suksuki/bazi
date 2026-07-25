from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent.world import compile_chart_world


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def chart_fact_hash(*, fixture: dict[str, Any], reading_id: str) -> str:
    birth = dict(fixture["birth_input"])
    # Synthetic fixtures encode explicit pillars and may use a sentinel rather
    # than a clock time. The benchmark ledger still needs a valid neutral clock.
    birth["birth_time"] = "12:00"
    world = compile_chart_world(
        reading_id=reading_id,
        birth_input=BirthInputCanonical.model_validate(birth),
        include_research_fixture_prior=False,
    )
    ledger = {
        "pillars": world.pillars,
        "birth_profile": world.birth_profile,
        "facts": [row.model_dump(mode="json") for row in world.facts],
        "boundaries": world.boundaries,
    }
    return canonical_hash(ledger)


def validate_phase0_assets(
    *,
    taxonomy_path: Path,
    development_path: Path,
    model_selection_path: Path,
    formal_manifest_path: Path,
    expert_reference_path: Path,
    reality_evidence_path: Path,
) -> dict[str, Any]:
    taxonomy = load_json(taxonomy_path)
    known_ids = {row["case_id"] for row in taxonomy["cases"]}
    development = load_json(development_path)
    model_selection = load_json(model_selection_path)
    formal = load_json(formal_manifest_path)
    expert = load_json(expert_reference_path)
    reality = load_json(reality_evidence_path)

    development_ids = _ids(development["cases"])
    selection_ids = _ids(model_selection["cases"])
    formal_ids = _ids(formal["cases"])
    expert_ids = {row["chart_id"] for row in expert["references"]}
    reality_ids = {row["chart_id"] for row in reality["packets"]}
    all_selected = development_ids | selection_ids | formal_ids

    errors: list[str] = []
    if len(development_ids) != len(development["cases"]):
        errors.append("duplicate_development_case")
    if len(selection_ids) != len(model_selection["cases"]):
        errors.append("duplicate_model_selection_case")
    if len(formal_ids) != 10 or len(formal_ids) != len(formal["cases"]):
        errors.append("formal_manifest_must_have_ten_unique_cases")
    if development_ids & selection_ids:
        errors.append("development_overlaps_model_selection")
    if development_ids & formal_ids:
        errors.append("development_overlaps_formal")
    if selection_ids & formal_ids:
        errors.append("model_selection_overlaps_formal")
    if all_selected - known_ids:
        errors.append(f"unknown_case_ids:{','.join(sorted(all_selected - known_ids))}")
    if expert_ids != formal_ids:
        errors.append("expert_reference_ids_do_not_match_formal_manifest")
    if reality_ids != formal_ids:
        errors.append("reality_packet_ids_do_not_match_formal_manifest")
    if any(_contains_reality_fields(row) for row in expert["references"]):
        errors.append("round1_expert_reference_contains_reality_evidence")

    fact_hashes: dict[str, str] = {}
    fixtures = {row["case_id"]: row for row in taxonomy["cases"]}
    for case_id in sorted(formal_ids):
        fact_hashes[case_id] = chart_fact_hash(
            fixture=fixtures[case_id],
            reading_id=f"phase0-g1-fact-hash:{case_id}",
        )
    reference_hash_mismatches = [
        row["chart_id"]
        for row in expert["references"]
        if row.get("chart_fact_hash") and row["chart_fact_hash"] != fact_hashes[row["chart_id"]]
    ]
    if reference_hash_mismatches:
        errors.append(f"expert_reference_fact_hash_mismatch:{','.join(sorted(reference_hash_mismatches))}")

    return {
        "valid": not errors,
        "errors": errors,
        "development_ids": sorted(development_ids),
        "model_selection_ids": sorted(selection_ids),
        "formal_ids": sorted(formal_ids),
        "chart_fact_hashes": fact_hashes,
        "expert_reference_frozen": expert_reference_is_frozen(expert=expert, fact_hashes=fact_hashes),
        "reality_evidence_frozen": reality_evidence_is_frozen(reality=reality),
    }


def expert_reference_is_frozen(*, expert: dict[str, Any], fact_hashes: dict[str, str]) -> bool:
    if expert.get("status") != "frozen":
        return False
    required_lists = (
        "must_notice",
        "acceptable_primary_hypotheses",
        "strongest_alternatives",
        "critical_relations",
        "plausible_work_paths",
        "conditional_useful_roles",
        "conditional_harmful_roles",
        "required_domain_distinctions",
        "unsupported_claims",
        "unresolved_disagreements",
    )
    for row in expert.get("references", []):
        if row.get("status") != "frozen" or not row.get("author") or not row.get("frozen_at"):
            return False
        if row.get("chart_fact_hash") != fact_hashes.get(row.get("chart_id")):
            return False
        if any(not row.get(field) for field in required_lists):
            return False
    return True


def reality_evidence_is_frozen(*, reality: dict[str, Any]) -> bool:
    if reality.get("status") != "frozen":
        return False
    return all(
        row.get("status") == "frozen"
        and row.get("author")
        and row.get("frozen_at")
        and row.get("source_provenance")
        for row in reality.get("packets", [])
    )


def build_formal_run_lock_candidate(
    *,
    root: Path,
    run_id: str,
    asset_paths: dict[str, Path],
    asset_validation: dict[str, Any],
    git_state_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lane_policy = load_json(asset_paths["lane_policy"])
    frontier_policy = load_json(asset_paths["frontier_policy"])
    go_no_go = load_json(asset_paths["go_no_go"])
    holistic_policy = load_json(asset_paths["holistic_synthesis_policy"])
    git_state = dict(git_state_override) if git_state_override is not None else _git_state(root)
    blockers: list[str] = []
    if not asset_validation["valid"]:
        blockers.append("phase0_asset_validation_failed")
    if not asset_validation["expert_reference_frozen"]:
        blockers.append("round1_expert_reference_not_human_frozen")
    if frontier_policy.get("status") != "frozen" or not frontier_policy.get("selected_policy"):
        blockers.append("true_frontier_policy_not_frozen")
    expected_lanes = [
        "direct_same_model",
        "direct_frontier",
        "current_v50",
        "fact_only_deepbazi",
        "holistic_synthesis",
        "vnext",
    ]
    actual_lanes = [row.get("lane_id") for row in lane_policy.get("formal_lanes", [])]
    if actual_lanes != expected_lanes:
        blockers.append("six_formal_lane_policy_invalid")
    if lane_policy.get("status") != "frozen_for_formal_run":
        blockers.append("lane_policy_not_frozen_for_formal_run")
    if holistic_policy.get("status") != "frozen_for_phase0_formal_run":
        blockers.append("holistic_synthesis_policy_not_frozen")
    if go_no_go.get("status") != "frozen_before_formal_outputs":
        blockers.append("go_no_go_thresholds_not_frozen")
    if not git_state["v50_snapshot_tracked"]:
        blockers.append("v50_code_snapshot_not_committed")

    return {
        "version": "deepbazi.vnext_phase0.formal_run_lock.v1",
        "run_id": run_id,
        "status": "frozen" if not blockers else "candidate_blocked",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_state["commit"],
        "dirty_tree": git_state["dirty_tree"],
        "git_state": git_state,
        "asset_hashes": {name: file_hash(path) for name, path in sorted(asset_paths.items())},
        "benchmark_manifest_hash": file_hash(asset_paths["formal_manifest"]),
        "expert_reference_hash": file_hash(asset_paths["expert_reference"]),
        "reality_evidence_hash": file_hash(asset_paths["reality_evidence"]),
        "lane_policy_hash": file_hash(asset_paths["lane_policy"]),
        "frontier_policy_hash": file_hash(asset_paths["frontier_policy"]),
        "dependency_lock_hash": file_hash(asset_paths["dependency_lock"]),
        "chart_fact_hashes": asset_validation["chart_fact_hashes"],
        "lane_definitions": lane_policy["formal_lanes"],
        "model_policy": {
            "same_model": lane_policy["same_model_policy"],
            "frontier": frontier_policy.get("selected_policy"),
        },
        "model_policy_hashes": {
            "same_model_and_lane_policy": file_hash(asset_paths["lane_policy"]),
            "frontier_policy": file_hash(asset_paths["frontier_policy"]),
        },
        "prompt_hashes": {
            "shared_benchmark_prompt_and_schema": file_hash(asset_paths["benchmark_contract"]),
            "vnext_context_compiler": file_hash(asset_paths["context_compiler"]),
        },
        "context_policy_hashes": {
            "lane_policy": file_hash(asset_paths["lane_policy"]),
            "holistic_synthesis_policy": file_hash(asset_paths["holistic_synthesis_policy"]),
            "vnext_context_compiler": file_hash(asset_paths["context_compiler"]),
        },
        "review_policy_hashes": {
            "deterministic_review_and_repair": file_hash(asset_paths["cognitive_reasoner"]),
            "fact_review": file_hash(asset_paths["fact_review"]),
            "modality_policy": file_hash(asset_paths["modality_policy"]),
            "promotion_gates": file_hash(asset_paths["go_no_go"]),
        },
        "execution_policy": lane_policy["execution_policy"],
        "retry_policy": {
            key: lane_policy["execution_policy"][key]
            for key in (
                "network_retry_limit",
                "timeout_retry_limit",
                "schema_mechanical_repair_limit",
                "manual_best_of_n_selection_allowed",
                "fact_hallucination_retry_allowed",
            )
        },
        "fact_engine_version": f"chart_world_sha256:{file_hash(asset_paths['fact_engine'])[:20]}",
        "review_policy": go_no_go["review_policy"],
        "promotion_gates_hash": file_hash(asset_paths["go_no_go"]),
        "blockers": blockers,
        "boundaries": {
            "formal_execution_allowed": not blockers,
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_rules_modified": False,
            "theory_modified": False,
            "professional_winner_claimed": False,
        },
    }


def validate_frozen_formal_lock(*, lock_path: Path, asset_paths: dict[str, Path]) -> dict[str, Any]:
    lock = load_json(lock_path)
    errors: list[str] = []
    if lock.get("status") != "frozen" or lock.get("blockers"):
        errors.append("formal_lock_not_frozen")
    locked_hashes = lock.get("asset_hashes", {})
    for name, path in asset_paths.items():
        if locked_hashes.get(name) != file_hash(path):
            errors.append(f"asset_hash_changed:{name}")
    return {"valid": not errors, "errors": errors, "lock": lock}


def _ids(rows: list[dict[str, Any]]) -> set[str]:
    return {row["case_id"] for row in rows}


def _contains_reality_fields(row: dict[str, Any]) -> bool:
    forbidden = {"known_reality_evidence", "reality_observations", "historical_years", "probe_answers"}
    return bool(forbidden & set(row))


def _git_state(root: Path) -> dict[str, Any]:
    try:
        top = Path(
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True).strip()
        )
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        relative = root.resolve().relative_to(top.resolve())
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--", str(relative)], cwd=top, text=True
        ).splitlines()
    except (OSError, subprocess.CalledProcessError, ValueError):
        return {
            "commit": "unavailable",
            "dirty_tree": True,
            "v50_status": ["git_state_unavailable"],
            "v50_snapshot_tracked": False,
        }
    tracked = not any(line.startswith("??") for line in status)
    return {
        "commit": commit,
        "dirty_tree": bool(status),
        "v50_status": status,
        "v50_snapshot_tracked": tracked and not status,
    }
