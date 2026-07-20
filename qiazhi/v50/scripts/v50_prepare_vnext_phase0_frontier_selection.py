from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.mingli_agent.phase0_governance import load_json
from scripts.v50_run_vnext_phase0_benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "vnext_phase0_frontier_candidates_v1.json"
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "frontier-selection-v1"
SELECTION_MANIFEST = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_model_policy_selection_set_v1.json"
SELECTION_FIXTURES = ROOT / "data" / "validation" / "phase0" / "vnext_phase0_model_policy_selection_fixture_pack_v1.json"


def prepare_selection(
    *, policy_path: Path, output_dir: Path, execute: bool, run_id: str
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    policy = load_json(policy_path)
    audit = validate_candidate_policy(policy=policy)
    _write_json(output_dir / "FRONTIER_CANDIDATE_POLICY_AUDIT.json", audit)
    if execute and audit["status"] != "passed":
        raise ValueError(f"frontier_candidate_execution_rejected:{','.join(audit['errors'])}")

    candidate_reports: list[dict[str, Any]] = []
    if execute:
        for candidate in policy["candidates"]:
            candidate_dir = output_dir / "candidate-runs" / candidate["candidate_id"]
            report = run_benchmark(
                run_id=f"{run_id}-{candidate['candidate_id']}",
                live=True,
                dry_run=True,
                model_selection_run=True,
                repeats=int(policy["selection_repeats"]),
                selected_lanes=["direct_frontier"],
                base_url=candidate["base_url"],
                same_model="not_used_in_frontier_selection",
                frontier_base_url=candidate["base_url"],
                frontier_model=candidate["model"],
                frontier_kind="true_frontier",
                frontier_max_tokens=int(candidate["token_budget"]),
                selected_case_ids=[],
                retry_failures=False,
                output_dir=candidate_dir,
                manifest_path=SELECTION_MANIFEST,
                fixture_pack_path=SELECTION_FIXTURES,
            )
            candidate_reports.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "policy_sha256": _canonical_hash(candidate),
                    "report_path": str(candidate_dir / "vnext_phase0_benchmark_report_v1.json"),
                    "status": report["status"],
                    "observed_data": report["observed_data"],
                    "rows": report["run_rows"],
                }
            )

    packet, operator_map = build_blind_selection_packet(candidate_reports=candidate_reports, run_id=run_id)
    _write_json(output_dir / "FRONTIER_SELECTION_BLIND_PACKET.json", packet)
    _write_json(output_dir / "FRONTIER_SELECTION_OPERATOR_MAP.json", operator_map)
    (output_dir / "FRONTIER_SELECTION_REVIEW.md").write_text(
        _review_markdown(packet=packet, candidate_count=len(policy.get("candidates", []))), encoding="utf-8"
    )
    status = (
        "selection_outputs_ready_for_human_review"
        if execute and candidate_reports and all(row["status"] == "passed" for row in candidate_reports)
        else "candidate_execution_partial"
        if execute
        else "pending_candidate_configuration"
        if not policy.get("candidates")
        else "candidate_policy_validated_not_executed"
    )
    report = {
        "version": "deepbazi.vnext_phase0.frontier_selection_preparation.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "candidate_policy_audit": audit,
        "candidate_count": len(policy.get("candidates", [])),
        "selection_case_count": len(load_json(SELECTION_MANIFEST)["cases"]),
        "selection_repeats": policy["selection_repeats"],
        "live_execution_performed": execute,
        "candidate_reports": [
            {key: value for key, value in row.items() if key != "rows"} for row in candidate_reports
        ],
        "human_selection_required": True,
        "selected_candidate": None,
        "formal_or_development_chart_accessed": False,
        "expert_reference_accessed": False,
        "reality_evidence_accessed": False,
        "automatic_winner_claimed": False,
    }
    _write_json(output_dir / "FRONTIER_SELECTION_REPORT.json", report)
    return report


def validate_candidate_policy(*, policy: dict[str, Any]) -> dict[str, Any]:
    contract = policy.get("candidate_contract", {})
    required = contract.get("required_fields", [])
    errors: list[str] = []
    ids: list[str] = []
    for index, candidate in enumerate(policy.get("candidates", [])):
        prefix = f"candidate:{index}"
        for field in required:
            if candidate.get(field) in (None, "", []):
                errors.append(f"missing_required_field:{prefix}:{field}")
        ids.append(str(candidate.get("candidate_id") or ""))
        if candidate.get("provider") != contract.get("supported_provider"):
            errors.append(f"unsupported_provider:{prefix}")
        if candidate.get("frontier_kind") != contract.get("frontier_kind_required"):
            errors.append(f"not_true_frontier:{prefix}")
        if candidate.get("structured_output_policy") != "CognitiveBenchmarkReading":
            errors.append(f"wrong_output_contract:{prefix}")
        if candidate.get("mechanical_repair_policy") != "schema_only_no_semantic_repair":
            errors.append(f"semantic_repair_not_prohibited:{prefix}")
        attestation = candidate.get("access_attestation") or {}
        if not attestation.get("strong_general_model_user_accessible"):
            errors.append(f"frontier_access_not_attested:{prefix}")
        if not attestation.get("attested_by") or not attestation.get("attested_at"):
            errors.append(f"frontier_attestation_incomplete:{prefix}")
        if candidate.get("temperature") != 0.2 or candidate.get("top_p") != 0.9:
            errors.append(f"sampling_policy_not_supported_by_current_runner:{prefix}")
        if candidate.get("context_window") != 32768 or candidate.get("timeout_seconds") != 360:
            errors.append(f"runtime_policy_not_supported_by_current_runner:{prefix}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate_candidate_id")
    if int(policy.get("selection_repeats", 0)) != 3:
        errors.append("selection_repeats_must_equal_three")
    return {
        "version": "deepbazi.vnext_phase0.frontier_candidate_policy_audit.v1",
        "status": "passed" if policy.get("candidates") and not errors else "pending" if not errors else "failed",
        "candidate_count": len(policy.get("candidates", [])),
        "errors": _unique(errors),
        "selection_manifest_sha256": sha256(SELECTION_MANIFEST.read_bytes()).hexdigest(),
        "selection_fixture_sha256": sha256(SELECTION_FIXTURES.read_bytes()).hexdigest(),
    }


def build_blind_selection_packet(
    *, candidate_reports: list[dict[str, Any]], run_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    operator: dict[str, Any] = {}
    candidate_codes: dict[str, str] = {}
    for report in candidate_reports:
        candidate_id = report["candidate_id"]
        candidate_code = candidate_codes.setdefault(
            candidate_id,
            f"FC-{sha256(f'{run_id}|{candidate_id}'.encode()).hexdigest()[:8].upper()}",
        )
        for row in report["rows"]:
            if row.get("status") != "completed":
                continue
            row_key = row["key"]
            case_id = row["case_id"]
            output_hash = sha256(f"{run_id}|{candidate_id}|{row_key}".encode()).hexdigest()[:12].upper()
            chart_hash = sha256(f"{run_id}|{case_id}".encode()).hexdigest()[:8].upper()
            output_code = f"FO-{output_hash}"
            outputs.append(
                {
                    "output_code": output_code,
                    "candidate_code": candidate_code,
                    "chart_code": f"SC-{chart_hash}",
                    "repeat": row["repeat"],
                    "pillars": row["pillars"],
                    "reading": row.get("raw_cognitive_output") or row["reading"],
                    "review": {
                        "professional_cognition": None,
                        "fact_reliability": None,
                        "specificity": None,
                        "falsifiability": None,
                        "notes": "",
                    },
                }
            )
            operator[output_code] = {
                "candidate_id": candidate_id,
                "candidate_code": candidate_code,
                "case_id": row["case_id"],
                "repeat": row["repeat"],
                "raw_cognitive_output_sha256": row.get("raw_cognitive_output_sha256"),
            }
    packet = {
        "version": "deepbazi.vnext_phase0.frontier_selection_blind_packet.v1",
        "outputs": sorted(outputs, key=lambda row: row["output_code"]),
        "candidate_summary_review": [
            {
                "candidate_code": code,
                "professional_cognition": None,
                "three_run_stability": None,
                "operational_reliability": None,
                "latency": None,
                "cost": None,
                "eligible_for_freeze": None,
                "notes": "",
            }
            for code in sorted(candidate_codes.values())
        ],
        "selected_candidate_code": None,
        "selection_reason": "",
        "reviewer": "",
        "reviewed_at": "",
    }
    return packet, operator


def freeze_selected_policy(
    *, candidate_policy_path: Path, reviewed_packet_path: Path, operator_map_path: Path, output_path: Path
) -> dict[str, Any]:
    policy = load_json(candidate_policy_path)
    packet = load_json(reviewed_packet_path)
    operator = load_json(operator_map_path)
    selected_code = packet.get("selected_candidate_code")
    errors: list[str] = []
    if not selected_code:
        errors.append("selected_candidate_code_missing")
    if not packet.get("selection_reason") or not packet.get("reviewer") or not packet.get("reviewed_at"):
        errors.append("human_selection_metadata_incomplete")
    summaries = {row["candidate_code"]: row for row in packet.get("candidate_summary_review", [])}
    selected_summary = summaries.get(selected_code)
    if not selected_summary or selected_summary.get("eligible_for_freeze") is not True:
        errors.append("selected_candidate_not_human_approved")
    for row in packet.get("outputs", []):
        if any(row.get("review", {}).get(field) is None for field in ("professional_cognition", "fact_reliability", "specificity", "falsifiability")):
            errors.append(f"output_review_incomplete:{row.get('output_code')}")
    candidate_ids = {
        value["candidate_id"] for value in operator.values() if value.get("candidate_code") == selected_code
    }
    if len(candidate_ids) != 1:
        errors.append("selected_candidate_mapping_invalid")
    if errors:
        raise ValueError(f"frontier_policy_freeze_rejected:{','.join(_unique(errors))}")
    selected_id = next(iter(candidate_ids))
    candidate = next(row for row in policy["candidates"] if row["candidate_id"] == selected_id)
    frozen = {
        "version": "deepbazi.vnext_phase0.frontier_policy.v2",
        "status": "frozen",
        "selection_set": str(SELECTION_MANIFEST.relative_to(ROOT)),
        "selected_policy": candidate,
        "candidate_policies": policy["candidates"],
        "freeze_metadata": {
            "selected_at": packet["reviewed_at"],
            "selected_by": packet["reviewer"],
            "selection_reason": packet["selection_reason"],
            "review_packet_hash": sha256(reviewed_packet_path.read_bytes()).hexdigest(),
            "operator_map_hash": sha256(operator_map_path.read_bytes()).hexdigest(),
        },
    }
    _write_json(output_path, frozen)
    return {"status": "frozen_candidate_written", "path": str(output_path), "selected_candidate_id": selected_id}


def _review_markdown(*, packet: dict[str, Any], candidate_count: int) -> str:
    return f"""# Frontier Selection Human Review

- Candidate count: `{candidate_count}`
- Output count: `{len(packet['outputs'])}`
- Selection charts: `5`
- Repeats per candidate: `3`

Review the blinded JSON packet. Score every output for professional cognition, fact reliability, specificity, and falsifiability. Then complete candidate-level stability, operational reliability, latency, and cost. Schema compliance alone cannot select a policy.

No candidate is automatically promoted. The operator map remains separate until human review is complete.
"""


def _canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or execute isolated Frontier policy selection.")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--run-id", default="frontier-selection-v1")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--freeze-reviewed-packet", default="")
    parser.add_argument("--operator-map", default="")
    parser.add_argument("--frozen-output", default="")
    args = parser.parse_args()
    if args.freeze_reviewed_packet:
        if not args.operator_map or not args.frozen_output:
            raise ValueError("freeze_requires_operator_map_and_frozen_output")
        result = freeze_selected_policy(
            candidate_policy_path=Path(args.policy),
            reviewed_packet_path=Path(args.freeze_reviewed_packet),
            operator_map_path=Path(args.operator_map),
            output_path=Path(args.frozen_output),
        )
    else:
        result = prepare_selection(
            policy_path=Path(args.policy), output_dir=Path(args.output_dir), execute=args.execute, run_id=args.run_id
        )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
