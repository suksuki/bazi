from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from scripts.v50_prepare_vnext_phase0_expert_reference_workspace import prepare_workspace
from scripts.v50_prepare_vnext_phase0_frontier_selection import DEFAULT_POLICY, prepare_selection
from scripts.v50_prepare_vnext_phase0_g1_7 import prepare_g1_7
from scripts.v50_prepare_vnext_phase0_snapshot import prepare_snapshot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "phase0-g1-8-workbench-v1"


def prepare_g1_8(
    *,
    run_id: str,
    output_dir: Path,
    git_state_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    g1_7 = prepare_g1_7(
        run_id=f"{run_id}-g1-7-refresh",
        output_dir=output_dir / "g1-7-refresh",
        git_state_override=git_state_override,
    )
    expert = prepare_workspace(output_dir=output_dir / "human-expert-reference")
    frontier = prepare_selection(
        policy_path=DEFAULT_POLICY,
        output_dir=output_dir / "frontier-selection",
        execute=False,
        run_id=f"{run_id}-frontier-selection",
    )
    snapshot = prepare_snapshot(
        output_dir=output_dir / "execution-snapshot",
        freeze=False,
        git_state_override=git_state_override,
    )

    machine_deliverables = {
        "human_reference_authoring_workspace": expert["status"] == "workspace_ready_for_human_authoring",
        "frontier_selection_harness": frontier["status"] in {
            "pending_candidate_configuration",
            "candidate_policy_validated_not_executed",
        },
        "execution_snapshot_manifest": snapshot["status"] in {"candidate_blocked", "candidate_ready_to_freeze"},
        "g1_7_policy_gates": all(g1_7["machine_gates"].values()),
    }
    external_inputs = {
        "human_expert_reference_completed": False,
        "true_frontier_candidate_configured": frontier["candidate_count"] > 0,
        "clean_committed_snapshot_available": snapshot["status"] == "frozen",
    }
    report = {
        "version": "deepbazi.vnext_phase0.g1_8_external_freeze_workbench.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": (
            "machine_workbench_complete_external_inputs_pending"
            if all(machine_deliverables.values())
            else "machine_workbench_revision_required"
        ),
        "ready_for_p0_g2": False,
        "machine_deliverables": machine_deliverables,
        "external_inputs": external_inputs,
        "observed_data": {
            "expert_workspace": expert,
            "frontier_selection": frontier,
            "execution_snapshot": {
                "status": snapshot["status"],
                "source_manifest_sha256": snapshot["source_manifest_sha256"],
                "file_count": snapshot["scope"]["file_count"],
                "blockers": snapshot["blockers"],
            },
            "g1_7_status": g1_7["status"],
            "g1_7_external_gates": g1_7["external_gates"],
        },
        "final_nonsealed_live_preflight": {
            "status": "prohibited_pending_external_inputs",
            "performed": False,
            "automatic_execution_allowed": False,
            "explicit_human_approval_required_after_all_freezes": True,
        },
        "next_actions": [
            "Human Mingli expert completes and signs the ten-chart authoring workspace.",
            "Operator adds at least one attested true Frontier policy and runs the five-chart three-repeat selection.",
            "Human reviewer completes the blinded Frontier packet and freezes one reproducible policy.",
            "Create a clean committed V50 snapshot without reverting unrelated work.",
            "Request explicit approval for one final non-sealed live preflight; do not start P0-G2 automatically.",
        ],
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "ui_modified": False,
            "expert_reference_authored_by_machine": False,
            "frontier_candidate_fabricated": False,
            "automatic_frontier_winner_selected": False,
            "automatic_git_commit_performed": False,
            "live_model_calls_performed": False,
            "sealed_formal_charts_executed": False,
            "p0_g2_started": False,
        },
    }
    _write_json(output_dir / "MASTER_AUDIT_REPORT.json", report)
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text(_markdown(report), encoding="utf-8")
    (output_dir / "HUMAN_HANDOFF.md").write_text(_human_handoff(report), encoding="utf-8")
    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    _write_json(
        output_dir / "ARTIFACT_MANIFEST.json",
        {
            "version": "deepbazi.vnext_phase0.g1_8_artifact_manifest.v1",
            "run_id": run_id,
            "files": [
                {
                    "path": str(path.relative_to(output_dir)),
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                }
                for path in files
            ],
        },
    )
    return report


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# VNext Phase 0 P0-G1.8 Master Audit Report",
            "",
            f"- Status: `{report['status']}`",
            "- Ready for P0-G2: `false`",
            "- Live model calls: `false`",
            "- Sealed formal charts executed: `false`",
            "",
            "## Machine Deliverables",
            "",
            *[f"- {key}: `{'passed' if value else 'failed'}`" for key, value in report["machine_deliverables"].items()],
            "",
            "## External Inputs",
            "",
            *[f"- {key}: `{'complete' if value else 'pending'}`" for key, value in report["external_inputs"].items()],
            "",
            "## What is now automatic",
            "",
            "- Expert worksheet generation, fact hashing, forbidden-field scanning, strict freeze validation and candidate writing.",
            "- Five-chart Frontier policy validation, three-repeat execution mode, blind packet generation and reviewed-policy freezing.",
            "- Phase 0 source manifest hashing and committed-snapshot refusal when Git is not clean.",
            "",
            "## What remains human or external",
            "",
            *[f"- {item}" for item in report["next_actions"]],
            "",
            "The workbench is complete. Professional content, external model access, model preference, and the Git commit are intentionally not fabricated.",
            "",
        ]
    )


def _human_handoff(report: dict[str, Any]) -> str:
    return """# P0-G1.8 Human Handoff

## Expert Reference

Open `human-expert-reference/EXPERT_REFERENCE_AUTHORING_WORKSPACE.json`, fill every semantic list with human-authored items, set each record to `frozen`, and add author, frozen_at, and human_signature. Then run strict validation and produce a frozen candidate.

## Frontier selection

Add reproducible attested candidates to `config/vnext_phase0_frontier_candidates_v1.json`. Run the selection tool with `--execute`; it will use only the five selection charts and three repeats. Complete the blinded packet before freezing one candidate.

## Snapshot and preflight

Commit a clean V50 snapshot without changing unrelated legacy work. Regenerate the snapshot with `--freeze`. Only after all three gates close may a human explicitly approve one non-sealed live preflight. P0-G2 does not start automatically.
"""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the complete P0-G1.8 external freeze workbench.")
    parser.add_argument("--run-id", default="phase0-g1-8-workbench-v1")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = prepare_g1_8(run_id=args.run_id, output_dir=Path(args.output_dir))
    print(json.dumps({"status": report["status"], "ready_for_p0_g2": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
