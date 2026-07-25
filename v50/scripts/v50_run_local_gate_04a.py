from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from core.mingli_agent.contracts import ChartWorldInstance
from core.mingli_agent.professional_review import (
    PROFESSIONAL_REVIEW_VERSION,
    review_professional_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_RUN = ROOT / "reports/local-gate-03/20260722-local-gate-03-v1"
DEFAULT_CORPUS = ROOT / "data/validation/fixtures/professional_failure_corpus_v1.json"
DEFAULT_OUTPUT = ROOT / "reports/local-gate-04a/20260722-local-gate-04a-v1"
FIXED_REVIEWED_AT = "2026-07-22T00:00:00+00:00"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _review_text(text: str, *, world: ChartWorldInstance, ref: str) -> dict[str, Any]:
    bundle = review_professional_payload(
        payload={"first_look": text, "evidence_refs": []},
        world=world,
        cognitive_record_ref=ref,
        created_at=FIXED_REVIEWED_AT,
        raw_source_kind="fixture_raw_payload",
    )
    return {
        "text": text,
        "release_status": bundle.overlay.professional_release_status,
        "hard_issue_classes": sorted(
            item.issue_class for item in bundle.overlay.issues if item.severity == "hard"
        ),
        "issue_classes": sorted({item.issue_class for item in bundle.overlay.issues}),
    }


def run_gate(
    *,
    source_run: Path = DEFAULT_SOURCE_RUN,
    corpus_path: Path = DEFAULT_CORPUS,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    expected_total = 0
    caught_total = 0
    first_world: ChartWorldInstance | None = None

    for case in corpus["cases"]:
        case_dir = source_run / case["source_directory"]
        raw_path = case_dir / "raw_model_output.json"
        stored_path = case_dir / "stored_case.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        world = ChartWorldInstance.model_validate(
            json.loads(stored_path.read_text(encoding="utf-8"))["world"]
        )
        first_world = first_world or world
        before = _canonical_hash(raw)
        bundle = review_professional_payload(
            payload=raw,
            world=world,
            cognitive_record_ref=case["case_id"],
            created_at=FIXED_REVIEWED_AT,
            raw_source_kind="fixture_raw_payload",
        )
        after = _canonical_hash(raw)
        detected = {item.issue_class for item in bundle.overlay.issues}
        expected = {item["issue_class"] for item in case["issues"]}
        caught = expected & detected
        expected_total += len(expected)
        caught_total += len(caught)
        cases.append({
            "case_id": case["case_id"],
            "original_machine_status": case["original_machine_status"],
            "human_verdict": case["human_verdict"],
            "assertion_count": len(bundle.assertions),
            "new_professional_release_status": (
                bundle.overlay.professional_release_status
            ),
            "downstream_domains_blocked": (
                bundle.overlay.downstream_domains_blocked
            ),
            "hard_error_count": bundle.overlay.hard_error_count,
            "major_error_count": bundle.overlay.major_error_count,
            "expected_issue_classes": sorted(expected),
            "detected_issue_classes": sorted(detected),
            "caught_expected_count": len(caught),
            "missed_expected_issue_classes": sorted(expected - detected),
            "raw_file_sha256": _sha256_file(raw_path),
            "raw_canonical_sha256": before,
            "review_raw_output_sha256": bundle.overlay.raw_output_hash,
            "raw_source_kind": bundle.overlay.raw_source_kind,
            "raw_output_unchanged": before == after,
            "semantic_auto_repair_count": 0,
        })

    if first_world is None:
        raise ValueError("professional_failure_corpus_empty")

    known_errors = [
        _review_text(
            "辛金生助丁火。",
            world=first_world,
            ref="local-gate-04a:known:five-element",
        ),
        _review_text(
            "酉午半合火局已经成立。",
            world=first_world,
            ref="local-gate-04a:known:branch-relation",
        ),
        _review_text(
            "原局构成双财生杀（食伤）之局。",
            world=first_world,
            ref="local-gate-04a:known:ontology",
        ),
    ]
    near_neighbors = [
        _review_text(
            "乙木生丁火，丁火克辛金。",
            world=first_world,
            ref="local-gate-04a:near:stem-flow",
        ),
        _review_text(
            "酉丑半合金局作为结构候选存在。",
            world=first_world,
            ref="local-gate-04a:near:metal-half-combination",
        ),
        _review_text(
            "寅午半合火局作为结构候选存在。",
            world=first_world,
            ref="local-gate-04a:near:fire-half-combination",
        ),
        _review_text(
            "丑中辛金七杀参与，丁火制杀。",
            world=first_world,
            ref="local-gate-04a:near:explicit-hidden-killing",
        ),
    ]
    modality_examples = [
        _review_text(
            "有人说：“辛金生助丁火。”",
            world=first_world,
            ref="local-gate-04a:modality:quoted",
        ),
        _review_text(
            "辛金是否生助丁火？",
            world=first_world,
            ref="local-gate-04a:modality:question",
        ),
        _review_text(
            "如果辛金生助丁火，另一条路径会怎样？",
            world=first_world,
            ref="local-gate-04a:modality:conditional",
        ),
        _review_text(
            "辛金并非生助丁火。",
            world=first_world,
            ref="local-gate-04a:modality:negated",
        ),
    ]

    domain_bundle = review_professional_payload(
        payload={"career": {"claim": "辛金生助丁火。"}},
        world=first_world,
        cognitive_record_ref="local-gate-04a:scope:domain",
        created_at=FIXED_REVIEWED_AT,
        raw_source_kind="fixture_raw_payload",
    )
    individual_bundle = review_professional_payload(
        payload={
            "selected_hypothesis_id": "h1",
            "hypotheses": [
                {
                    "hypothesis_id": "h1",
                    "status": "primary",
                    "confidence": "medium",
                    "thesis": "乙木生丁火，丁火克辛金。",
                    "success_conditions": ["乙木与丁火均参与结构。"],
                    "failure_conditions": [],
                    "evidence_refs": [],
                },
                {
                    "hypothesis_id": "h2",
                    "status": "alternative",
                    "confidence": "low",
                    "thesis": "辛金生助丁火。",
                    "success_conditions": [],
                    "failure_conditions": [],
                    "evidence_refs": [],
                },
            ],
        },
        world=first_world,
        cognitive_record_ref="local-gate-04a:scope:individual",
        created_at=FIXED_REVIEWED_AT,
        raw_source_kind="fixture_raw_payload",
    )

    blocked_cases = sum(
        item["new_professional_release_status"] == "blocked" for item in cases
    )
    raw_rewrites = sum(not item["raw_output_unchanged"] for item in cases)
    near_neighbor_hard_false_positives = sum(
        bool(item["hard_issue_classes"]) for item in near_neighbors
    )
    modality_false_blocks = sum(
        item["release_status"] != "passed" for item in modality_examples
    )
    scope_isolation_passed = bool(
        domain_bundle.overlay.professional_release_status == "partially_blocked"
        and domain_bundle.overlay.downstream_domains_blocked is False
        and [(item.scope, item.scope_ref) for item in domain_bundle.overlay.scope_blocks]
        == [("domain", "career")]
        and individual_bundle.overlay.professional_release_status == "partially_blocked"
        and individual_bundle.overlay.downstream_domains_blocked is False
    )
    status = "PASS" if all((
        blocked_cases == len(cases),
        caught_total == expected_total,
        raw_rewrites == 0,
        near_neighbor_hard_false_positives == 0,
        modality_false_blocks == 0,
        scope_isolation_passed,
    )) else "FAIL"

    summary: dict[str, Any] = {
        "version": "deepbazi.local_gate_04a_summary.v1",
        "run_id": "20260722-local-gate-04a-v1",
        "status": status,
        "review_version": PROFESSIONAL_REVIEW_VERSION,
        "source_corpus": {
            "path": str(corpus_path.relative_to(ROOT)),
            "file_sha256": _sha256_file(corpus_path),
            "content_hash": corpus["corpus_content_hash"],
            "source_run_id": corpus["source_run_id"],
        },
        "totals": {
            "cases": len(cases),
            "original_machine_committed": corpus["machine_committed_count"],
            "original_human_safe": corpus["human_safe_count"],
            "new_professional_blocked": blocked_cases,
            "frozen_expected_issue_classes": expected_total,
            "caught_expected_issue_classes": caught_total,
            "missed_expected_issue_classes": expected_total - caught_total,
            "raw_semantic_rewrites": raw_rewrites,
            "known_hard_examples_caught": sum(
                bool(item["hard_issue_classes"]) for item in known_errors
            ),
            "near_neighbor_hard_false_positives": near_neighbor_hard_false_positives,
            "modality_false_blocks": modality_false_blocks,
        },
        "scope_isolation": {
            "core_block_blocks_downstream_domains": all(
                item["downstream_domains_blocked"] for item in cases
            ),
            "domain_block_only": {
                "release_status": domain_bundle.overlay.professional_release_status,
                "scope_blocks": [
                    item.model_dump(mode="json")
                    for item in domain_bundle.overlay.scope_blocks
                ],
            },
            "individual_assertion_suppression": {
                "release_status": individual_bundle.overlay.professional_release_status,
                "suppressed_assertion_count": len(
                    individual_bundle.overlay.suppressed_assertion_refs
                ),
                "downstream_domains_blocked": (
                    individual_bundle.overlay.downstream_domains_blocked
                ),
            },
            "passed": scope_isolation_passed,
        },
        "known_hard_examples": known_errors,
        "correct_near_neighbors": near_neighbors,
        "modality_examples": modality_examples,
        "cases": cases,
        "boundaries": {
            "reasoner_modified": False,
            "prompt_modified": False,
            "graph_modified": False,
            "onecanvas_modified": False,
            "ui_modified": False,
            "llm_used": False,
            "semantic_auto_repair_allowed": False,
            "professional_quality_of_reasoner": "still_failed_not_repaired",
            "next_phase_entered": False,
        },
    }
    summary["summary_content_hash"] = _canonical_hash(summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "local_gate_04a_summary.json"
    report_path = output_dir / "LOCAL_GATE_04A_ASSERTION_INTEGRITY.md"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_render_markdown(summary), encoding="utf-8")
    manifest = {
        "version": "deepbazi.local_gate_04a_manifest.v1",
        "run_id": summary["run_id"],
        "inputs": {
            str(corpus_path.relative_to(ROOT)): _sha256_file(corpus_path),
            str((source_run / "manifest.sha256.json").relative_to(ROOT)): (
                _sha256_file(source_run / "manifest.sha256.json")
            ),
        },
        "outputs": {
            summary_path.name: _sha256_file(summary_path),
            report_path.name: _sha256_file(report_path),
        },
        "reproduce": (
            "PYTHONPATH=packages:apps:tests python "
            "scripts/v50_run_local_gate_04a.py"
        ),
    }
    (output_dir / "manifest.sha256.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _render_markdown(summary: dict[str, Any]) -> str:
    totals = summary["totals"]
    lines = [
        "# LOCAL-GATE-04A Assertion Integrity Gate",
        "",
        f"- Status: `{summary['status']}`",
        f"- Review contract: `{summary['review_version']}`",
        f"- Failure Corpus: `{summary['source_corpus']['content_hash']}`",
        "- LLM used: `false`",
        "- Semantic auto-repair: `0`",
        "",
        "## Gate Result",
        "",
        "| Check | Result |",
        "| --- | ---: |",
        f"| Former false releases now blocked | {totals['new_professional_blocked']}/{totals['cases']} |",
        f"| Frozen human issue classes caught | {totals['caught_expected_issue_classes']}/{totals['frozen_expected_issue_classes']} |",
        f"| Correct near-neighbor hard false positives | {totals['near_neighbor_hard_false_positives']} |",
        f"| Modality false blocks | {totals['modality_false_blocks']} |",
        f"| Raw semantic rewrites | {totals['raw_semantic_rewrites']} |",
        "",
        "## Five-Chart Replay",
        "",
        "| Case | Typed Assertions | Release | Hard | Expected caught | Raw unchanged |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for case in summary["cases"]:
        lines.append(
            f"| `{case['case_id']}` | {case['assertion_count']} | "
            f"`{case['new_professional_release_status']}` | "
            f"{case['hard_error_count']} | {case['caught_expected_count']}/"
            f"{len(case['expected_issue_classes'])} | "
            f"`{str(case['raw_output_unchanged']).lower()}` |"
        )
    lines.extend([
        "",
        "## Release Isolation",
        "",
        "- Core errors block the whole-chart professional release and downstream domains.",
        "- Domain errors block only their named domain.",
        "- Individual errors remain in immutable source evidence and are omitted from formal projection.",
        "- Persisted state and professional release state are independent.",
        "- Legacy `committed` data without a ProfessionalReviewOverlay is `unreviewed`, not formal.",
        "- A professionally blocked cached baseline is reused with zero additional model calls.",
        "",
        "## Boundary",
        "",
        "04A detects, records, suppresses, and blocks. It does not rewrite cognition. "
        "Reasoner quality remains failed and was not modified; 04B was not entered.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run_gate(
        source_run=args.source_run,
        corpus_path=args.corpus,
        output_dir=args.output,
    )
    print(json.dumps({
        "status": summary["status"],
        "summary_content_hash": summary["summary_content_hash"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
