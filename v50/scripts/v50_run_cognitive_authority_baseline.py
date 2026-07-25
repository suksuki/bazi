from __future__ import annotations

import argparse
import json
import time
from copy import deepcopy
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliAgent, MingliCognitiveDraft, MingliContextCompiler, compile_chart_world
from core.mingli_agent.quality import compare_cognitive_distinction, evaluate_cognitive_quality
from core.mingli_agent.reasoner import review_cognition


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "validation" / "fixtures"
MANIFEST_PATH = FIXTURE_DIR / "cognitive_authority_baseline_v1.json"
TAXONOMY_PATH = FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json"
DEFAULT_REPORT_DIR = ROOT / "reports" / "cognitive-authority-baseline" / "v1"


class BenchmarkOnlyToolAnchoredCompiler(MingliContextCompiler):
    """Recreates the retired tool-anchored first look for controlled comparison only."""

    FACT_LIMITS = deepcopy(MingliContextCompiler.FACT_LIMITS)
    FACT_LIMITS["pattern"] = {
        "graph_relation": 12,
        "candidate_path": 5,
        "candidate_node_role": 5,
        "estimated_sensitivity": 4,
        "tool_salience": 4,
    }


def run_baseline(
    *,
    run_id: str = "offline",
    live: bool = False,
    live_limit: int = 0,
    external_comparison_path: str = "",
    reuse_live_path: str = "",
    live_splits: list[str] | None = None,
    live_case_ids: list[str] | None = None,
    live_checkpoint_path: str = "",
) -> dict[str, Any]:
    manifest = _load(MANIFEST_PATH)
    taxonomy = _load(TAXONOMY_PATH)
    case_map = {item["case_id"]: item for item in taxonomy["cases"]}
    split_map = {
        case_id: split
        for split in ("development", "acceptance", "blind")
        for case_id in manifest[split]
    }
    ordered_ids = [
        *manifest["development"],
        *manifest["acceptance"],
        *manifest["blind"],
    ]
    default_compiler = MingliContextCompiler()
    legacy_compiler = BenchmarkOnlyToolAnchoredCompiler()
    offline_rows: list[dict[str, Any]] = []
    worlds: dict[str, Any] = {}
    for case_id in ordered_ids:
        fixture = case_map[case_id]
        world = compile_chart_world(
            reading_id=f"authority-baseline:{run_id}:{case_id}",
            birth_input=_birth(fixture),
            include_research_fixture_prior=False,
        )
        worlds[case_id] = world
        independent = default_compiler.compile(world=world, stage="pattern")
        challenge = default_compiler.compile(world=world, stage="work_path")
        legacy = legacy_compiler.compile(world=world, stage="pattern")
        offline_rows.append({
            "case_id": case_id,
            "case_type": fixture["case_type"],
            "split": split_map[case_id],
            "pillars": world.pillars,
            "independent_pattern_fact_count": len(independent.fact_refs),
            "independent_pattern_experimental_tool_refs": independent.experimental_tool_refs,
            "challenge_pack_experimental_tool_count": len(challenge.experimental_tool_refs),
            "benchmark_only_legacy_tool_injection_count": len(legacy.experimental_tool_refs),
            "independent_context_bytes": _bytes(independent.payload),
            "challenge_context_bytes": _bytes(challenge.payload),
            "expected_contract_visible_to_model": False,
        })

    if reuse_live_path:
        live_rows = _reuse_live(path=reuse_live_path, worlds=worlds)
        if live and live_case_ids:
            rerun_rows = _run_live(
                manifest=manifest,
                case_map=case_map,
                worlds=worlds,
                run_id=run_id,
                live=True,
                live_limit=0,
                live_splits=live_splits or ["development", "acceptance", "blind"],
                live_case_ids=live_case_ids,
                checkpoint_path=live_checkpoint_path,
            )
            merged = {row["case_id"]: row for row in live_rows}
            merged.update({row["case_id"]: row for row in rerun_rows})
            live_rows = list(merged.values())
    else:
        live_rows = _run_live(
            manifest=manifest,
            case_map=case_map,
            worlds=worlds,
            run_id=run_id,
            live=live,
            live_limit=live_limit,
            live_splits=live_splits or ["development", "acceptance", "blind"],
            live_case_ids=live_case_ids or [],
            checkpoint_path=live_checkpoint_path,
        )
    pairwise = _pairwise_distinction(live_rows)
    external = _external_comparison(external_comparison_path)
    leaks = [row["case_id"] for row in offline_rows if row["independent_pattern_experimental_tool_refs"]]
    missing_challenge = [row["case_id"] for row in offline_rows if row["challenge_pack_experimental_tool_count"] == 0]
    live_failures = [row["case_id"] for row in live_rows if row["status"] != "completed"]
    hard_fact_conflict_cases = [
        row["case_id"]
        for row in live_rows
        if row.get("variants", {}).get("facts_first", {}).get("quality_signals", {}).get("factual_conflict_hits")
    ]
    unsupported_fact_claim_cases = [
        row["case_id"]
        for row in live_rows
        if row.get("variants", {}).get("facts_first", {}).get("quality_signals", {}).get("unsupported_fact_claim_hits")
    ]
    strict_review_failure_cases = [
        row["case_id"]
        for row in live_rows
        if row.get("variants", {}).get("facts_first", {}).get("strict_epistemic_review", {}).get("passed") is False
    ]
    completed_live_ids = {row["case_id"] for row in live_rows if row["status"] == "completed"}
    expert_review_ready = set(manifest["blind"]).issubset(completed_live_ids)
    live_requested = live or bool(reuse_live_path)
    run_integrity_status = "passed" if not leaks and (not live_requested or not live_failures) else "partial"
    report = {
        "version": "deepbazi.cognitive_authority_baseline_report.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": run_integrity_status,
        "run_integrity_status": run_integrity_status,
        "professional_quality_status": "pending_expert_review",
        "ready_for_cognitive_promotion": False,
        "observed_data": {
            "case_count": len(offline_rows),
            "split_counts": {split: len(manifest[split]) for split in ("development", "acceptance", "blind")},
            "structure_family_count": len({row["case_type"] for row in offline_rows}),
            "independent_pattern_tool_leak_count": len(leaks),
            "challenge_pack_missing_count": len(missing_challenge),
            "avg_independent_context_bytes": round(mean(row["independent_context_bytes"] for row in offline_rows)),
            "avg_challenge_context_bytes": round(mean(row["challenge_context_bytes"] for row in offline_rows)),
            "live_case_count": len(live_rows),
            "live_split_counts": {
                split: sum(row["case_id"] in manifest[split] for row in live_rows)
                for split in ("development", "acceptance", "blind")
            },
            "live_failure_count": len(live_failures),
            "hard_fact_conflict_case_count": len(hard_fact_conflict_cases),
            "hard_fact_conflict_case_ids": hard_fact_conflict_cases,
            "unsupported_fact_claim_case_count": len(unsupported_fact_claim_cases),
            "unsupported_fact_claim_case_ids": unsupported_fact_claim_cases,
            "strict_epistemic_review_failure_case_count": len(strict_review_failure_cases),
            "strict_epistemic_review_failure_case_ids": strict_review_failure_cases,
            "external_comparison_loaded": bool(external),
        },
        "offline_context_audit": offline_rows,
        "live_cognitive_results": live_rows,
        "pairwise_distinction": pairwise,
        "external_comparison": external,
        "expert_review_packet": {
            "status": (
                "ready_for_blind_review"
                if expert_review_ready
                else "development_outputs_ready" if live_rows else "awaiting_live_outputs"
            ),
            "blind_case_ids": manifest["blind"],
            "rubric": manifest["human_rubric"],
            "automated_scores_are_professional_gold": False,
            "blind_live_output_count": len(set(manifest["blind"]) & completed_live_ids),
        },
        "interpretation": {
            "observed": "Pattern 第一眼只读取不可变事实与中性关系；Graph/Path/Role/敏感度只在第二阶段以实验性挑战材料出现。",
            "inference": "这修复了认知权威顺序，但自动指标不能证明命理判断已经专业正确。",
            "next_gate": (
                "先重跑确定性事实冲突样本，再进行命理师盲审与 V30/人工结果对比。"
                if hard_fact_conflict_cases
                else "确定性硬冲突已清零；世界模型未覆盖的关系主张单列为研究缺口，下一门禁是命理师盲审与 V30/人工结果对比。"
            ),
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified_during_run": False,
            "mingli_algorithm_modified_during_run": False,
            "theory_modified": False,
            "expected_contract_visible_to_model": False,
            "self_generated_output_promoted_to_gold": False,
            "automated_quality_used_as_professional_judge": False,
        },
    }
    return report


def _run_live(
    *,
    manifest: dict[str, Any],
    case_map: dict[str, dict[str, Any]],
    worlds: dict[str, Any],
    run_id: str,
    live: bool,
    live_limit: int,
    live_splits: list[str],
    live_case_ids: list[str],
    checkpoint_path: str,
) -> list[dict[str, Any]]:
    if not live:
        return []
    candidates = [case_id for split in live_splits for case_id in manifest[split]]
    if live_case_ids:
        requested = set(live_case_ids)
        candidates = [case_id for case_id in candidates if case_id in requested]
        unknown = requested - set(candidates)
        if unknown:
            raise ValueError(f"unknown_live_case_ids:{','.join(sorted(unknown))}")
    if live_limit > 0:
        candidates = candidates[:live_limit]
    facts_first_agent = MingliAgent(context_compiler=MingliContextCompiler())
    checkpoint = Path(checkpoint_path) if checkpoint_path else None
    recovered = _load_checkpoint(checkpoint) if checkpoint else {}
    rows: list[dict[str, Any]] = [recovered[case_id] for case_id in candidates if case_id in recovered]
    for case_id in candidates:
        if case_id in recovered:
            continue
        fixture = case_map[case_id]
        world = worlds[case_id]
        row: dict[str, Any] = {
            "case_id": case_id,
            "case_type": fixture["case_type"],
            "status": "completed",
            "variants": {},
        }
        started = time.monotonic()
        try:
            record = facts_first_agent.first_reading(case_id=f"{run_id}:facts_first:{case_id}", world=world)
            quality = evaluate_cognitive_quality(record, world=world)
            strict_review = review_cognition(draft=record.cognition, world=world, model=record.model)
            row["variants"]["facts_first"] = {
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "first_look": record.cognition.first_look,
                "whole_chart_thesis": record.cognition.whole_chart_thesis,
                "selected_hypothesis_id": record.cognition.selected_hypothesis_id,
                "work_path": record.cognition.work_path.path_statement,
                "work_path_origin": record.cognition.work_path.origin,
                "quality_signals": quality.model_dump(mode="json"),
                "strict_epistemic_review": strict_review.model_dump(mode="json"),
                "cognition": record.cognition.model_dump(mode="json"),
            }
        except Exception as exc:  # noqa: BLE001 - a benchmark records failures and never repairs inline.
            row["status"] = "failed"
            row["variants"]["facts_first"] = {
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "error": f"{type(exc).__name__}:{exc}",
            }
        rows.append(row)
        if checkpoint:
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            with checkpoint.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(
            json.dumps(
                {"case_id": case_id, "status": row["status"], "completed_cases": len(rows)},
                ensure_ascii=False,
            ),
            flush=True,
        )
    return rows


def _load_checkpoint(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    recovered: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        recovered[str(row["case_id"])] = row
    return recovered


def _pairwise_distinction(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    complete = [row for row in rows if "cognition" in row.get("variants", {}).get("facts_first", {})]
    return [
        {
            "left_case_id": left["case_id"],
            "right_case_id": right["case_id"],
            **compare_cognitive_distinction(
                left["variants"]["facts_first"]["cognition"],
                right["variants"]["facts_first"]["cognition"],
            ).model_dump(mode="json"),
        }
        for left, right in combinations(complete, 2)
    ]


def _reuse_live(*, path: str, worlds: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source in (item.strip() for item in path.split(",") if item.strip()):
        saved = _load(Path(source))
        for row in saved.get("live_cognitive_results", []):
            merged[str(row["case_id"])] = deepcopy(row)
    rows = list(merged.values())
    for row in rows:
        world = worlds.get(row.get("case_id"))
        if world is None:
            row["status"] = "failed"
            row["reuse_error"] = "case_not_present_in_current_manifest"
            continue
        for variant in row.get("variants", {}).values():
            cognition = variant.get("cognition")
            if cognition:
                variant["quality_signals"] = evaluate_cognitive_quality(
                    cognition,
                    world=world,
                ).model_dump(mode="json")
                variant["strict_epistemic_review"] = review_cognition(
                    draft=MingliCognitiveDraft.model_validate(cognition),
                    world=world,
                    model="recomputed_without_llm_call",
                ).model_dump(mode="json")
        variants = row.get("variants", {})
        row["reused_without_llm_call"] = True
    return rows


def _external_comparison(path: str) -> dict[str, Any]:
    if not path:
        return {}
    payload = _load(Path(path))
    return {
        "source_path": str(Path(path).resolve()),
        "source_declared_by_user": True,
        "case_count": len(payload.get("cases", [])),
        "payload": payload,
    }


def _birth(fixture: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(fixture["birth_input"])
    payload["birth_time"] = "12:00"
    return BirthInputCanonical.model_validate(payload)


def _bytes(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(report: dict[str, Any], *, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cognitive_authority_baseline_v1.json"
    md_path = output_dir / "cognitive_authority_baseline_v1.md"
    review_path = output_dir / "cognitive_authority_expert_review_packet_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    observed = report["observed_data"]
    md_path.write_text(
        "\n".join([
            "# Cognitive Authority Baseline v1",
            "",
            f"- Status: `{report['status']}`",
            f"- Professional quality: `{report['professional_quality_status']}`",
            f"- Ready for cognitive promotion: `{str(report['ready_for_cognitive_promotion']).lower()}`",
            f"- Cases: `{observed['case_count']}`",
            f"- Splits: `{observed['split_counts']}`",
            f"- Structure families: `{observed['structure_family_count']}`",
            f"- Independent-pattern tool leaks: `{observed['independent_pattern_tool_leak_count']}`",
            f"- Missing challenge packs: `{observed['challenge_pack_missing_count']}`",
            f"- Live cases: `{observed['live_case_count']}` / failures `{observed['live_failure_count']}`",
            f"- Hard fact-conflict cases: `{observed['hard_fact_conflict_case_count']}`",
            f"- Unsupported fact-claim cases: `{observed['unsupported_fact_claim_case_count']}`",
            f"- Strict epistemic-review failures: `{observed['strict_epistemic_review_failure_case_count']}`",
            "",
            "## Interpretation",
            "",
            f"- Observed: {report['interpretation']['observed']}",
            f"- Inference: {report['interpretation']['inference']}",
            f"- Next gate: {report['interpretation']['next_gate']}",
            "",
            "## Expert Review",
            "",
            f"- Status: `{report['expert_review_packet']['status']}`",
            f"- Blind cases: `{len(report['expert_review_packet']['blind_case_ids'])}`",
            "- Automated scores are professional gold: `false`",
            "",
            "## Boundaries",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]),
        encoding="utf-8",
    )
    review_path.write_text(_expert_review_markdown(report), encoding="utf-8")
    return json_path, md_path, review_path


def _expert_review_markdown(report: dict[str, Any]) -> str:
    manifest = _load(MANIFEST_PATH)
    split_by_case = {
        case_id: split
        for split in ("development", "acceptance", "blind")
        for case_id in manifest[split]
    }
    lines = [
        "# Cognitive Authority Expert Review Packet v1",
        "",
        "本包不包含 synthetic expected contract。自动指标只用于定位风险，不是命理专业评分。",
        "",
        f"- Run integrity: `{report['run_integrity_status']}`",
        f"- Professional quality: `{report['professional_quality_status']}`",
        f"- Ready for promotion: `{str(report['ready_for_cognitive_promotion']).lower()}`",
        "",
        "## Review Scale",
        "",
        "每项 0-5 分：盘面重心、竞争假设、主做功、用神条件性、事实可靠性、可证伪性、跨盘区分度。",
        "最终结论只允许：`prefer` / `revise` / `reject` / `insufficient`。",
        "",
    ]
    if not report["live_cognitive_results"]:
        lines.extend(["暂无 live 认知结果。", ""])
        return "\n".join(lines)
    for row in report["live_cognitive_results"]:
        variant = row.get("variants", {}).get("facts_first", {})
        quality = variant.get("quality_signals", {})
        strict_review = variant.get("strict_epistemic_review", {})
        lines.extend([
            f"## {row['case_id']}",
            "",
            f"- Split: `{split_by_case.get(row['case_id'], 'unknown')}`",
            f"- Structure family: `{row['case_type']}`",
            f"- Status: `{row['status']}`",
            f"- Elapsed: `{variant.get('elapsed_seconds', 'n/a')}s`",
            "",
        ])
        if row["status"] != "completed":
            lines.extend([f"- Failure: `{variant.get('error', 'unknown')}`", ""])
            continue
        lines.extend([
            "### 第一眼",
            "",
            str(variant.get("first_look", "")),
            "",
            "### 整盘主论",
            "",
            str(variant.get("whole_chart_thesis", "")),
            "",
            "### 主做功",
            "",
            str(variant.get("work_path", "")),
            "",
            "### 自动诊断（非专业评分）",
            "",
            f"- Structural specificity: `{quality.get('structural_specificity')}`",
            f"- Falsifiability: `{quality.get('falsifiability')}`",
            f"- Fact traceability: `{quality.get('fact_traceability')}`",
            f"- Deterministic fact consistency: `{quality.get('deterministic_fact_consistency')}`",
            f"- Fact conflicts: `{quality.get('factual_conflict_hits', [])}`",
            f"- Unsupported fact claims: `{quality.get('unsupported_fact_claim_hits', [])}`",
            f"- Strict review passed: `{strict_review.get('passed')}`",
            f"- Strict review issues: `{strict_review.get('issues', [])}`",
            f"- Generic-language risk: `{quality.get('generic_language_risk')}`",
            f"- Warnings: `{quality.get('warnings', [])}`",
            "",
            "### 人工审阅",
            "",
            "```yaml",
            "salience: null",
            "hypothesis_comparison: null",
            "work_path_coherence: null",
            "useful_god_conditionality: null",
            "fact_reliability: null",
            "falsifiability: null",
            "cross_chart_distinction: null",
            "decision: null",
            "notes: ''",
            "```",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical V50 cognitive-authority baseline.")
    parser.add_argument("--run-id", default="offline")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--live-limit", type=int, default=0)
    parser.add_argument("--live-splits", nargs="*", choices=["development", "acceptance", "blind"], default=["development", "acceptance", "blind"])
    parser.add_argument("--live-case-ids", nargs="*", default=[], help="Run or rerun only these manifest case ids.")
    parser.add_argument("--external-comparison", default="")
    parser.add_argument("--reuse-live", default="", help="Recompute diagnostics from a previous baseline JSON without calling the LLM.")
    parser.add_argument("--output-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()
    report = run_baseline(
        run_id=args.run_id,
        live=args.live,
        live_limit=args.live_limit,
        external_comparison_path=args.external_comparison,
        reuse_live_path=args.reuse_live,
        live_splits=args.live_splits,
        live_case_ids=args.live_case_ids,
        live_checkpoint_path=str(Path(args.output_dir) / "live_checkpoint.jsonl") if args.live else "",
    )
    paths = write_report(report, output_dir=Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
