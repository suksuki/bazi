from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experience.canvas import (
    CanvasAction,
    CanvasCompileRequest,
    apply_canvas_action,
    compile_canvas_context,
    compile_canvas_diff,
    compile_canvas_spec,
    create_temporal_sandbox,
    load_canvas_compile_input,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "packages" / "experience" / "fixtures"
REPORT_DIR = ROOT / "reports" / "mingli-canvas-c0"


def audit() -> dict[str, Any]:
    source = load_canvas_compile_input(FIXTURES / "temporal_sandbox_c0_v1.json")
    natal_request = CanvasCompileRequest(source=source, stage="natal")
    natal = compile_canvas_spec(natal_request)
    natal_repeat = compile_canvas_spec(natal_request)
    luck = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="luck",
        luck_layer_id="luck-gengzi-official",
    ))
    formal_year = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="year",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
    ))
    natal_luck_diff = compile_canvas_diff(natal, luck, source_action_ref="audit:add-luck")
    luck_year_diff = compile_canvas_diff(luck, formal_year, source_action_ref="audit:add-year")

    sandbox = create_temporal_sandbox(
        sandbox_session_id="sandbox-c0-audit",
        base_snapshot_id="snapshot-year-bingwu-v1",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
    )
    action = CanvasAction(
        action_id="audit-replace-year",
        action_type="replace_year",
        target_layer_id="year-guimao-hypothetical",
        source_ref="audit:fixed-action",
    )
    modified = apply_canvas_action(source=source, sandbox=sandbox, action=action)
    hypothetical = compile_canvas_spec(CanvasCompileRequest(source=source, stage="year", sandbox=modified))
    hypothetical_repeat = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="year",
        sandbox=apply_canvas_action(source=source, sandbox=sandbox, action=action),
    ))
    formal_hypothetical_diff = compile_canvas_diff(
        formal_year,
        hypothetical,
        source_action_ref="audit:replace-year",
    )
    restored = apply_canvas_action(
        source=source,
        sandbox=modified,
        action=CanvasAction(action_id="audit-restore", action_type="restore", source_ref="audit:restore"),
    )
    restored_spec = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="year",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
        sandbox=restored,
    ))

    diff_source = load_canvas_compile_input(FIXTURES / "canvas_diff_semantics_c0_v1.json")
    diff_before = compile_canvas_spec(CanvasCompileRequest(source=diff_source, stage="natal"))
    diff_after = compile_canvas_spec(CanvasCompileRequest(
        source=diff_source,
        stage="luck",
        luck_layer_id="luck-diff-contract",
    ))
    semantic_diff = compile_canvas_diff(diff_before, diff_after, source_action_ref="audit:all-semantics")
    semantic_counts = {
        "introduced": len(semantic_diff.introduced_paths),
        "removed": len(semantic_diff.removed_paths),
        "activated": len(semantic_diff.activated_paths),
        "reinforced": len(semantic_diff.reinforced_paths),
        "weakened": len(semantic_diff.weakened_paths),
        "blocked": len(semantic_diff.blocked_paths),
        "reopened": len(semantic_diff.reopened_paths),
        "unchanged": len(semantic_diff.unchanged_paths),
    }

    selected_refs = [
        "path-committed-output-pressure",
        "path-candidate-direct-earth",
        "path-blocked-template-reading",
        "relation-hyp-gui-controls-ding",
    ]
    contexts = {
        role: compile_canvas_context(
            spec=hypothetical,
            diff=formal_hypothetical_diff,
            role=role,
            selected_object_refs=selected_refs,
            visible_layers=["generation_control", "work_path"],
            sandbox=modified,
        )
        for role in ("member", "practitioner", "research")
    }

    traces = [
        *(item.trace for item in hypothetical.semantic_slots),
        *(item.trace for item in hypothetical.nodes),
        *(item.trace for item in hypothetical.relations),
        *(item.state_trace for item in hypothetical.relations),
        *(item.trace for item in hypothetical.clusters),
        *(item.trace for item in hypothetical.paths),
        *(item.state_trace for item in hypothetical.paths),
    ]
    checks = {
        "same_input_same_spec": natal == natal_repeat,
        "same_sandbox_replay_same_spec": hypothetical == hypothetical_repeat,
        "restore_returns_formal_spec": restored_spec == formal_year,
        "every_trace_has_source": all(item.source_refs for item in traces),
        "all_eight_diff_semantics_present": all(value == 1 for value in semantic_counts.values()),
        "natal_slots_remain_immutable": all(item.immutable for item in hypothetical.semantic_slots[:4]),
        "sandbox_does_not_write_chart": modified.writes_chart is False,
        "sandbox_does_not_write_life_case": modified.writes_life_case is False,
        "member_cannot_see_candidate": not contexts["member"].candidate_path_refs,
        "member_cannot_see_research_block": not contexts["member"].blocked_path_refs,
        "practitioner_sees_candidate_not_research_block": (
            contexts["practitioner"].candidate_path_refs == ["path-candidate-direct-earth"]
            and not contexts["practitioner"].blocked_path_refs
        ),
        "research_sees_blocked_path": contexts["research"].blocked_path_refs == ["path-blocked-template-reading"],
        "official_diffs_are_independent": (
            natal_luck_diff.to_spec_id == luck.identity.canvas_spec_id
            and luck_year_diff.from_spec_id == luck.identity.canvas_spec_id
        ),
    }
    passed = all(checks.values())
    return {
        "run_name": "Mingli Interactive Canvas C0 Contract Fixtures",
        "status": "passed" if passed else "failed",
        "c0_gate_passed": passed,
        "observed_data": {
            "baseline_spec_id": natal.identity.canvas_spec_id,
            "luck_spec_id": luck.identity.canvas_spec_id,
            "year_spec_id": formal_year.identity.canvas_spec_id,
            "hypothetical_spec_id": hypothetical.identity.canvas_spec_id,
            "formal_to_hypothetical_diff_id": formal_hypothetical_diff.diff_id,
            "semantic_diff_counts": semantic_counts,
            "trace_count": len(traces),
            "source_mode_counts": _counts(item.source_mode for item in traces),
            "epistemic_status_counts": _counts(item.epistemic_status for item in traces),
            "role_disclosure": {
                role: {
                    "committed_paths": context.committed_path_refs,
                    "candidate_paths": context.candidate_path_refs,
                    "blocked_paths": context.blocked_path_refs,
                    "disclosed_object_count": len(context.disclosed_object_refs),
                }
                for role, context in contexts.items()
            },
        },
        "checks": checks,
        "interpretation": (
            "C0 proves deterministic, traceable Spec/Diff/Context compilation without a renderer."
            if passed
            else "One or more C0 contract boundaries failed; C1 renderer work must remain blocked."
        ),
        "recommendation": "authorize C1 read-only six-pillar canvas" if passed else "repair C0 only",
        "boundary_status": {
            "runtime_modified": False,
            "reasoner_modified": False,
            "life_case_modified": False,
            "ui_modified": False,
            "mingli_algorithm_modified": False,
            "llm_used": False,
            "sandbox_writes_formal_state": False,
        },
        "reproduce_command": (
            "PYTHONPATH=packages:apps ../.venv/bin/python scripts/v50_audit_mingli_canvas_c0.py"
        ),
    }


def write_report(result: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "mingli_canvas_c0_audit_v1.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    checks = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} `{name}`"
        for name, passed in result["checks"].items()
    )
    boundaries = "\n".join(
        f"- `{name}`: `{str(value).lower()}`"
        for name, value in result["boundary_status"].items()
    )
    markdown = f"""# Mingli Interactive Canvas C0 Audit v1

Status: **{result['status'].upper()}**  
C0 Gate: **{'PASS' if result['c0_gate_passed'] else 'BLOCKED'}**

## Observed Data

```json
{json.dumps(result['observed_data'], ensure_ascii=False, indent=2)}
```

## Contract Checks

{checks}

## Interpretation

{result['interpretation']}

## Recommendation

`{result['recommendation']}`

## Boundary Status

{boundaries}

## Reproduce

```bash
{result['reproduce_command']}
```
"""
    (REPORT_DIR / "MASTER_AUDIT_REPORT.md").write_text(markdown, encoding="utf-8")


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


if __name__ == "__main__":
    outcome = audit()
    write_report(outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    raise SystemExit(0 if outcome["c0_gate_passed"] else 1)
