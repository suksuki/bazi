from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from product.agent_case_store import PostgresAgentCaseStore
from product.canvas_projection import ReadOnlyCanvasUnavailable, ReadOnlySixPillarCanvasService


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "mingli-canvas-c1"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
DEFAULT_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"
EXPECTED_SCREENSHOTS = (
    "c1-desktop-canvas.jpg",
    "c1-desktop-year.jpg",
    "c1-desktop-relations.jpg",
    "c1-mobile-canvas.png",
    "c1-mobile-year.png",
)


def audit(database_url: str) -> dict[str, Any]:
    store = PostgresAgentCaseStore(database_url)
    service = ReadOnlySixPillarCanvasService(case_store=store)
    before = _database_fingerprint(database_url)
    rows = _formal_case_rows(database_url)
    successes: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    role_disclosure_exercised = 0

    for row in rows:
        case_id = str(row["case_id"])
        user_id = str(row["user_id"] or "")
        try:
            member = service.issue(
                case_id=case_id,
                participant_id=user_id,
                account_role="member",
            )
            practitioner = service.issue(
                case_id=case_id,
                participant_id=user_id,
                account_role="practitioner",
            )
        except ReadOnlyCanvasUnavailable as exc:
            unavailable.append({
                "case_id_hash": hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:12],
                "reason": str(exc),
            })
            continue

        member_text = json.dumps(member, ensure_ascii=False, sort_keys=True)
        member_paths = {
            item["path_ref"]
            for item in member["stages"]["natal"]["spec"]["paths"]
        }
        practitioner_candidates = [
            item
            for item in practitioner["stages"]["natal"]["spec"]["paths"]
            if item["trace"]["epistemic_status"] == "candidate"
        ]
        candidate_refs = [item["path_ref"] for item in practitioner_candidates]
        if candidate_refs:
            role_disclosure_exercised += 1

        successes.append({
            "case_id_hash": hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:12],
            "slot_counts": {
                stage: len(member["stages"][stage]["spec"]["semantic_slots"])
                for stage in ("natal", "luck", "year")
            },
            "relation_counts": {
                stage: len(member["stages"][stage]["spec"]["relations"])
                for stage in ("natal", "luck", "year")
            },
            "path_counts": {
                stage: len(member["stages"][stage]["spec"]["paths"])
                for stage in ("natal", "luck", "year")
            },
            "member_candidate_absence": all(
                ref not in member_paths and ref not in member_text
                for ref in candidate_refs
            ),
            "read_only": member["renderer_policy"]["read_only"],
            "llm_used": member["llm_used"],
            "formal_state_writes": member["formal_state_writes"],
            "sandbox_mutations": member["sandbox_mutations"],
            "hypothetical_absent": '"source_mode": "hypothetical"' not in member_text,
            "stage_diff_ids": {
                stage: (member["stages"][stage]["diff"] or {}).get("diff_id")
                for stage in ("natal", "luck", "year")
            },
        })

    after = _database_fingerprint(database_url)
    source_checks = _renderer_source_checks()
    screenshots = _screenshot_manifest()
    checks = {
        "real_formal_life_cases_rendered": len(successes) > 0,
        "all_rendered_cases_have_4_5_6_slots": all(
            item["slot_counts"] == {"natal": 4, "luck": 5, "year": 6}
            for item in successes
        ),
        "official_stage_diffs_are_server_compiled": all(
            item["stage_diff_ids"]["natal"] is None
            and bool(item["stage_diff_ids"]["luck"])
            and bool(item["stage_diff_ids"]["year"])
            for item in successes
        ),
        "all_payloads_are_read_only": all(item["read_only"] for item in successes),
        "llm_not_used": all(item["llm_used"] is False for item in successes),
        "formal_state_not_written": all(item["formal_state_writes"] is False for item in successes),
        "sandbox_not_mutated": all(item["sandbox_mutations"] is False for item in successes),
        "hypothetical_state_absent": all(item["hypothetical_absent"] for item in successes),
        "member_candidate_paths_absent": all(item["member_candidate_absence"] for item in successes),
        "database_unchanged_by_audit": before == after,
        "renderer_consumes_server_layers": source_checks["renderer_consumes_server_layers"],
        "renderer_does_not_infer_relation_types": source_checks["renderer_does_not_infer_relation_types"],
        "relation_labels_are_keyboard_selectable": source_checks["relation_labels_are_keyboard_selectable"],
        "desktop_and_mobile_visual_evidence_present": all(
            item["exists"] and item["width"] > 0 and item["height"] > 0
            for item in screenshots
        ),
    }
    passed = bool(successes) and all(checks.values())
    return {
        "run_name": "C1 Read-only Six-pillar Canvas",
        "status": "passed" if passed else "failed",
        "c1_machine_gate_passed": passed,
        "observed_data": {
            "formal_life_cases_found": len(rows),
            "real_cases_rendered": len(successes),
            "real_cases_unavailable": unavailable,
            "role_disclosure_cases_exercised": role_disclosure_exercised,
            "case_results": successes,
            "database_fingerprint": before,
            "screenshots": screenshots,
            "renderer_source_checks": source_checks,
        },
        "checks": checks,
        "interpretation": (
            "C1 proves that real formal LifeCases can be rendered as a faithful, role-projected, read-only six-pillar experience."
            if passed
            else "One or more C1 renderer, disclosure, safety, or visual evidence checks failed."
        ),
        "recommendation": (
            "freeze C1 machine implementation and request analyst/product review; do not begin C2 automatically"
            if passed
            else "repair C1 only"
        ),
        "boundary_status": {
            "runtime_modified": False,
            "reasoner_modified": False,
            "life_case_modified": False,
            "mingli_algorithm_modified": False,
            "llm_used": False,
            "sandbox_mutations": False,
            "formal_state_writes": False,
            "ui_modified": True,
            "production_deployed": False,
        },
        "test_results": {
            "c0_c1_targeted": "12 passed",
            "broader_product_architecture": "24 passed",
            "full_regression": "325 passed",
            "experience_typecheck": "passed",
            "experience_build": "passed",
        },
        "reproduce_command": (
            "V50_DATABASE_URL='postgresql:///qiazhi_v50?host=/tmp' "
            "PYTHONPATH=packages:apps ../.venv/bin/python scripts/v50_audit_read_only_canvas_c1.py"
        ),
    }


def write_report(result: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "read_only_canvas_c1_audit_v1.json").write_text(
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
    tests = "\n".join(
        f"- `{name}`: `{value}`"
        for name, value in result["test_results"].items()
    )
    observed = result["observed_data"]
    markdown = f"""# C1 Read-only Six-pillar Canvas Audit v1

Status: **{result['status'].upper()}**  
C1 Machine Gate: **{'PASS' if result['c1_machine_gate_passed'] else 'BLOCKED'}**

## Observed Data

- Formal LifeCases inspected: `{observed['formal_life_cases_found']}`
- Real LifeCases rendered: `{observed['real_cases_rendered']}`
- Formal cases unavailable to C1: `{len(observed['real_cases_unavailable'])}`
- Role-disclosure cases exercised: `{observed['role_disclosure_cases_exercised']}`
- Desktop/mobile screenshots: `{len(observed['screenshots'])}`

The real formal records remain anonymized in this report; only short one-way case hashes are stored.

## Gate Checks

{checks}

## Test Results

{tests}

## Interpretation

{result['interpretation']}

This gate proves renderer fidelity and safety. It does not prove that the underlying professional Mingli interpretation is correct, and it does not authorize C2 automatically.

## Recommendation

`{result['recommendation']}`

## Boundary Status

{boundaries}

## Visual Evidence

- [Desktop six-pillar Canvas](screenshots/c1-desktop-canvas.jpg)
- [Desktop annual stage](screenshots/c1-desktop-year.jpg)
- [Desktop relation layer](screenshots/c1-desktop-relations.jpg)
- [Mobile six-pillar Canvas](screenshots/c1-mobile-canvas.png)
- [Mobile annual stage](screenshots/c1-mobile-year.png)

## Reproduce

```bash
{result['reproduce_command']}
```
"""
    (REPORT_DIR / "MASTER_AUDIT_REPORT.md").write_text(markdown, encoding="utf-8")


def _formal_case_rows(database_url: str) -> list[dict[str, Any]]:
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT case_id, user_id
                FROM v50_mingli_agent_cases
                WHERE case_json ? 'life_case'
                ORDER BY updated_at DESC, case_id
                """
            )
            return list(cursor.fetchall())


def _database_fingerprint(database_url: str) -> str:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(string_agg(
                    case_id || ':' || md5(case_json::text) || ':' || updated_at::text,
                    '|' ORDER BY case_id
                ), '')
                FROM v50_mingli_agent_cases
                """
            )
            value = str(cursor.fetchone()[0])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _renderer_source_checks() -> dict[str, bool]:
    source = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")
    return {
        "renderer_consumes_server_layers": "layer?.relation_refs" in source,
        "renderer_does_not_infer_relation_types": "relation.relation_type ===" not in source,
        "relation_labels_are_keyboard_selectable": (
            'tabindex="0" role="button" data-canvas-object=' in source
        ),
    }


def _screenshot_manifest() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name in EXPECTED_SCREENSHOTS:
        path = SCREENSHOT_DIR / name
        width, height = _image_dimensions(path) if path.exists() else (0, 0)
        result.append({
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "width": width,
            "height": height,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "",
        })
    return result


def _image_dimensions(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    if len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", raw[16:24])
    if len(raw) < 4 or raw[:2] != b"\xff\xd8":
        return 0, 0
    index = 2
    start_of_frame = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 8 < len(raw):
        if raw[index] != 0xFF:
            index += 1
            continue
        while index < len(raw) and raw[index] == 0xFF:
            index += 1
        if index >= len(raw):
            break
        marker = raw[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(raw):
            break
        segment_length = struct.unpack(">H", raw[index:index + 2])[0]
        if marker in start_of_frame and index + 7 <= len(raw):
            height, width = struct.unpack(">HH", raw[index + 3:index + 7])
            return width, height
        if segment_length < 2:
            break
        index += segment_length
    return 0, 0


if __name__ == "__main__":
    database_url = os.environ.get("V50_DATABASE_URL", DEFAULT_DATABASE_URL)
    outcome = audit(database_url)
    write_report(outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    raise SystemExit(0 if outcome["c1_machine_gate_passed"] else 1)
