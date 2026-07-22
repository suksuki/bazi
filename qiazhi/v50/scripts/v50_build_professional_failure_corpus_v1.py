from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = "deepbazi.professional_failure_corpus.v1"
DEFAULT_RUN = Path("reports/local-gate-03/20260722-local-gate-03-v1")
DEFAULT_OUTPUT = Path("data/validation/fixtures/professional_failure_corpus_v1.json")

ISSUES: dict[str, list[tuple[str, str, str]]] = {
    "c2_output_controls_pressure_01": [
        ("辛金七杀（被制/转化） -> 丑土财星（得生）", "work_path_transition_direction_error", "hard_block"),
        ("巳丑半合金局", "invalid_branch_relation", "suppress"),
    ],
    "c2_output_to_wealth_01": [
        ("子水正印扎根时支", "rooting_fact_error", "hard_block"),
        ("疏泄旺土之气并生助戊土", "work_path_internal_contradiction", "hard_block"),
        ("形成‘食神制杀/疏土’", "mechanism_required_role_missing", "hard_block"),
    ],
    "c2_month_command_dominant_01": [
        ("双财生杀（食伤）", "ontology_mechanism_role_conflict", "hard_block"),
        ("精神焦虑或健康隐患（心血管/眼目）", "unopened_health_domain_projection", "domain_block"),
    ],
    "c2_mixed_officer_killing_with_control_01": [
        ("‘岁运并临’式的六冲", "natal_timing_scope_conflict", "hard_block"),
        ("酉金与时支午火形成半合火局意向", "invalid_branch_relation", "hard_block"),
        ("午火（食神）", "ten_god_mapping_error", "hard_block"),
    ],
    "c2_climate_regulation_dominant_01": [
        ("时干辛金生助", "five_element_relation_error", "hard_block"),
        ("乙木偏印虽透干，但坐丑土受克", "five_element_control_direction_error", "suppress"),
        ("将湿土之气彻底转化为强金", "half_combination_overpromoted_to_transformation", "hard_block"),
    ],
}


def build_corpus(*, run_dir: Path) -> dict[str, Any]:
    manifest = run_dir / "manifest.sha256.json"
    content_audit = run_dir / "content_audit.json"
    audit_payload = json.loads(content_audit.read_text(encoding="utf-8"))
    audit_by_case = {
        str(item["case_id"]).replace(".", "_"): item
        for item in audit_payload["cases"]
    }
    cases: list[dict[str, Any]] = []
    for directory_name, issue_specs in ISSUES.items():
        raw_path = run_dir / directory_name / "raw_model_output.json"
        raw_bytes = raw_path.read_bytes()
        raw_payload = json.loads(raw_bytes)
        strings = list(_walk_strings(raw_payload))
        issue_rows = []
        for needle, issue_class, expected_disposition in issue_specs:
            matches = [
                (path, text.index(needle), text)
                for path, text in strings
                if needle in text
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"corpus_source_binding_not_unique:{directory_name}:{needle}:{len(matches)}"
                )
            field_path, start, source_text = matches[0]
            issue_rows.append({
                "issue_id": f"{directory_name}:{issue_class}:{len(issue_rows) + 1}",
                "issue_class": issue_class,
                "expected_disposition": expected_disposition,
                "field_path": field_path,
                "start": start,
                "end": start + len(needle),
                "source_text": needle,
                "source_field_hash": _sha(source_text.encode("utf-8")),
                "binding_status": "exact",
            })
        audit = audit_by_case[directory_name]
        cases.append({
            "case_id": audit["case_id"],
            "source_directory": directory_name,
            "raw_model_output_sha256": _sha(raw_bytes),
            "original_machine_status": "committed",
            "human_verdict": audit["decision"],
            "human_confidence": audit["confidence"],
            "issues": issue_rows,
        })
    payload: dict[str, Any] = {
        "version": VERSION,
        "corpus_id": "professional-failure-corpus-v1",
        "source_run_id": audit_payload["run_id"],
        "source_manifest_sha256": _sha(manifest.read_bytes()),
        "source_content_audit_sha256": _sha(content_audit.read_bytes()),
        "machine_committed_count": audit_payload["machine_committed"],
        "human_safe_count": audit_payload["safe_for_professional_submission"],
        "case_count": len(cases),
        "raw_outputs_embedded": False,
        "cases": cases,
        "boundaries": {
            "purpose": "Regression evidence for professional release isolation",
            "not_professional_gold": True,
            "raw_output_is_immutable": True,
            "semantic_auto_repair_allowed": False,
        },
    }
    payload["corpus_content_hash"] = _sha(_canonical_bytes(payload))
    return payload


def _walk_strings(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            yield from _walk_strings(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}.{index}")
    elif isinstance(value, str):
        yield path, value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_corpus(run_dir=args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "case_count": payload["case_count"],
        "corpus_content_hash": payload["corpus_content_hash"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
