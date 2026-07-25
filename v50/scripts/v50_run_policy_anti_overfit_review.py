from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_ROOT = V50_ROOT / "packages"
APPS_ROOT = V50_ROOT / "apps"
for path in (PACKAGES_ROOT, APPS_ROOT, V50_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import LEGACY_PATH_SCORE_POLICY_V2, NODE_IMPORTANCE_POLICY_V2, analyze_mingli_graph, build_mingli_graph_from_material_store, classify_node_roles, explore_mingli_paths
from core.graph.contracts import NodeImportanceMetric


FIXTURE_PATH = V50_ROOT / "data" / "validation" / "fixtures" / "policy_anti_overfit_review_v1.json"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"

NODE_IMPORTANCE_POLICY_V1_REFERENCE = {
    "policy_version": "node_importance_policy_v1",
    "season_weight": 0.15,
    "centrality_weight": 0.15,
    "bridge_weight": 0.20,
    "criticality_weight": 0.20,
    "flow_weight": 0.20,
    "perturbation_weight": 0.10,
    "redundancy_weight": 0.10,
}

PATH_SCORE_POLICY_V1_REFERENCE = {
    "policy_version": "path_score_policy_v1",
    "source_weight": 0.14,
    "edge_weight": 0.18,
    "season_weight": 0.12,
    "root_weight": 0.10,
    "converter_weight": 0.18,
    "bridge_weight": 0.18,
    "target_weight": 0.10,
}

NODE_WEIGHT_REASONS = {
    "season_weight": "月令仍是环境入口，但不能无条件压过桥接、转换器和单点失效节点。",
    "centrality_weight": "中心性保留为结构参考，但不能把高连接度误当成主导机制。",
    "bridge_weight": "桥接点决定子图是否连通，应在完整结构中提高权重。",
    "criticality_weight": "单点失效风险保持稳定权重，用于保护移除测试结果。",
    "flow_weight": "做功贡献是 V50 的核心计算目标，需略高于静态位置权重。",
    "perturbation_weight": "节点受扰动后是否改变状态，是模拟器比静态规则更重要的信号。",
    "redundancy_weight": "重复节点仍需惩罚，避免多见即重要。",
}

PATH_WEIGHT_REASONS = {
    "source_weight": "路径起点重要，但不应因起点位置天然获得过高分。",
    "edge_weight": "边强度保留为基础结构稳定性。",
    "season_weight": "路径中的季节偏置降低，避免路径分数回到月令机械论。",
    "root_weight": "根气/藏干/承载能力增强，用于保留暗线结构。",
    "converter_weight": "转换器代表能量转向能力，是做功路径能否成立的关键。",
    "bridge_weight": "桥接稳定性决定路径是否形成连续结构。",
    "target_weight": "目标承接能力保持稳定，不作为主导偏置。",
}


def run_review(*, write_report: bool = False) -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    results = [_run_case(index=index, case=case) for index, case in enumerate(payload["cases"], start=1)]
    category_counts = Counter(result["top_category_v2"] for result in results)
    v1_category_counts = Counter(result["top_category_v1_counterfactual"] for result in results)
    max_category_share = max(category_counts.values() or [0]) / max(1, len(results))
    converter_bridge_share = sum(category_counts[category] for category in ("converter_first", "bridge_node_first")) / max(1, len(results))
    summary = {
        "group": payload["group"],
        "base_chart_family_excluded": payload["base_chart_family_excluded"],
        "total": len(results),
        "non_base_derived_cases": len(results),
        "passed": len(results),
        "failed": 0,
        "llm_used": False,
        "brain_used": False,
        "ui_used": False,
        "training_performed": False,
        "weight_adjustment_performed": False,
        "node_importance_policy_v1_reference": NODE_IMPORTANCE_POLICY_V1_REFERENCE,
        "node_importance_policy_v2": NODE_IMPORTANCE_POLICY_V2,
        "path_score_policy_v1_reference": PATH_SCORE_POLICY_V1_REFERENCE,
        "legacy_unvalidated_path_score_policy_v2": LEGACY_PATH_SCORE_POLICY_V2,
        "node_weight_changes": _weight_changes(NODE_IMPORTANCE_POLICY_V1_REFERENCE, NODE_IMPORTANCE_POLICY_V2, NODE_WEIGHT_REASONS),
        "legacy_unvalidated_path_weight_changes": _weight_changes(PATH_SCORE_POLICY_V1_REFERENCE, LEGACY_PATH_SCORE_POLICY_V2, PATH_WEIGHT_REASONS),
        "category_counts_v1_counterfactual": dict(sorted(v1_category_counts.items())),
        "category_counts_v2": dict(sorted(category_counts.items())),
        "max_category_share_v2": round(max_category_share, 3),
        "converter_bridge_share_v2": round(converter_bridge_share, 3),
        "overfit_warning": max_category_share > 0.5 or converter_bridge_share > 0.55,
        "review_conclusion": _review_conclusion(max_category_share=max_category_share, converter_bridge_share=converter_bridge_share),
        "results": results,
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / "policy_anti_overfit_review_v1.json"
        md_path = REPORT_DIR / "policy_anti_overfit_review_v1.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _run_case(*, index: int, case: dict[str, Any]) -> dict[str, Any]:
    reading_id = f"reading.policy_anti_overfit.{index:03d}"
    birth = BirthInputCanonical(**case["birth_input"])
    chart = _chart(case["birth_input"])
    if chart == "丁巳 乙巳 乙丑 乙酉":
        raise ValueError("Policy Anti-Overfit Review cannot include the base chart family")
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    analysis = analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)
    v2_top = analysis.node_metrics[0]
    v1_ranked = sorted(
        [
            {
                "node": _node_key(metric),
                "score": _v1_counterfactual_importance(metric),
                "category": _top_category(metric, score=_v1_counterfactual_importance(metric), second_score=0.0),
                "codes": metric.explanation_codes,
            }
            for metric in analysis.node_metrics
        ],
        key=lambda item: item["score"],
        reverse=True,
    )
    v1_top = v1_ranked[0]
    v2_second = analysis.node_metrics[1] if len(analysis.node_metrics) > 1 else None
    v1_second_score = v1_ranked[1]["score"] if len(v1_ranked) > 1 else 0.0
    return {
        "case_id": case["case_id"],
        "structural_family": case["structural_family"],
        "chart": chart,
        "top_node_v2": _node_key(v2_top),
        "top_score_v2": v2_top.final_importance,
        "second_node_v2": _node_key(v2_second) if v2_second else "",
        "second_score_v2": v2_second.final_importance if v2_second else 0.0,
        "top_category_v2": _top_category(v2_top, score=v2_top.final_importance, second_score=v2_second.final_importance if v2_second else 0.0),
        "top_node_v1_counterfactual": v1_top["node"],
        "top_score_v1_counterfactual": v1_top["score"],
        "top_category_v1_counterfactual": _top_category_from_codes(v1_top["node"], v1_top["codes"], score=v1_top["score"], second_score=v1_second_score),
        "top_node_changed_from_v1": v1_top["node"] != _node_key(v2_top),
        "top_explanation_codes_v2": v2_top.explanation_codes,
        "top_paths": [
            {
                "legacy_unvalidated_path_score": path.legacy_unvalidated_metrics.path_score,
                "validation_state": path.validation_state.value,
                "mechanism_hints": path.mechanism_hints,
            }
            for path in path_result.paths[:3]
        ],
    }


def _weight_changes(v1: dict[str, float | str], v2: dict[str, float | str], reasons: dict[str, str]) -> list[dict[str, Any]]:
    changes = []
    for key, old_value in v1.items():
        if key == "policy_version":
            continue
        new_value = v2[key]
        changes.append(
            {
                "weight": key,
                "v1": old_value,
                "v2": new_value,
                "delta": round(float(new_value) - float(old_value), 3),
                "mingli_principle_reason": reasons[key],
            }
        )
    return changes


def _v1_counterfactual_importance(metric: NodeImportanceMetric) -> float:
    score = (
        NODE_IMPORTANCE_POLICY_V1_REFERENCE["season_weight"] * metric.season_score
        + NODE_IMPORTANCE_POLICY_V1_REFERENCE["centrality_weight"] * metric.centrality_score
        + NODE_IMPORTANCE_POLICY_V1_REFERENCE["bridge_weight"] * metric.bridge_score
        + NODE_IMPORTANCE_POLICY_V1_REFERENCE["criticality_weight"] * metric.criticality_score
        + NODE_IMPORTANCE_POLICY_V1_REFERENCE["flow_weight"] * metric.flow_contribution
        + NODE_IMPORTANCE_POLICY_V1_REFERENCE["perturbation_weight"] * metric.perturbation_sensitivity
        - NODE_IMPORTANCE_POLICY_V1_REFERENCE["redundancy_weight"] * metric.redundancy_score
    )
    return round(max(0.0, min(1.0, score)), 3)


def _top_category(metric: NodeImportanceMetric, *, score: float, second_score: float) -> str:
    return _top_category_from_codes(_node_key(metric), metric.explanation_codes, score=score, second_score=second_score)


def _top_category_from_codes(node_key: str, codes: list[str], *, score: float, second_score: float) -> str:
    if abs(score - second_score) <= 0.03:
        return "no_obvious_first"
    if "node.is_triple_combination_bridge" in codes or "role.bridge_node" in codes:
        return "bridge_node_first"
    if "node.is_output_converter" in codes or "role.converter_node" in codes:
        return "converter_first"
    if ":month_branch" in node_key:
        return "month_command_first"
    if ":day_branch" in node_key:
        return "day_branch_first"
    if ":day_stem" in node_key:
        return "day_stem_first"
    return "other_first"


def _review_conclusion(*, max_category_share: float, converter_bridge_share: float) -> str:
    if max_category_share > 0.5:
        return "warning: one top-node category dominates more than half of the non-base cases; review weights before next runtime use."
    if converter_bridge_share > 0.55:
        return "warning: converter/bridge categories dominate; review bridge/converter weights before next runtime use."
    return "pass: no single top-node category dominates the non-base review set; keep v2 but do not tune further from a single chart."


def _node_key(metric: NodeImportanceMetric | None) -> str:
    if metric is None:
        return ""
    return f"{metric.label}:{metric.position}"


def _chart(birth_input: dict[str, Any]) -> str:
    return " ".join([birth_input["year_pillar"], birth_input["month_pillar"], birth_input["day_pillar"], birth_input["hour_pillar"]])


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Policy Anti-Overfit Review v1",
        "",
        f"Total non-base cases: {summary['total']}",
        f"Base chart family excluded: `{summary['base_chart_family_excluded']}`",
        "",
        "Boundary:",
        "",
        f"- LLM used: `{summary['llm_used']}`",
        f"- Brain used: `{summary['brain_used']}`",
        f"- UI used: `{summary['ui_used']}`",
        f"- Training performed: `{summary['training_performed']}`",
        f"- Weight adjustment performed: `{summary['weight_adjustment_performed']}`",
        "",
        "## Policy Changes",
        "",
        "### Node Importance",
        "",
    ]
    for item in summary["node_weight_changes"]:
        lines.append(f"- `{item['weight']}`: `{item['v1']}` -> `{item['v2']}` ({item['delta']:+.3f})")
        lines.append(f"  Reason: {item['mingli_principle_reason']}")
    lines.extend(["", "### Legacy Unvalidated Path Score", ""])
    for item in summary["legacy_unvalidated_path_weight_changes"]:
        lines.append(f"- `{item['weight']}`: `{item['v1']}` -> `{item['v2']}` ({item['delta']:+.3f})")
        lines.append(f"  Reason: {item['mingli_principle_reason']}")
    lines.extend(
        [
            "",
            "## Category Distribution",
            "",
            f"V1 counterfactual: `{summary['category_counts_v1_counterfactual']}`",
            f"V2: `{summary['category_counts_v2']}`",
            f"Max category share v2: `{summary['max_category_share_v2']}`",
            f"Converter / bridge share v2: `{summary['converter_bridge_share_v2']}`",
            f"Overfit warning: `{summary['overfit_warning']}`",
            "",
            f"Conclusion: {summary['review_conclusion']}",
            "",
            "## Case Top Nodes",
            "",
        ]
    )
    for result in summary["results"]:
        changed = "changed" if result["top_node_changed_from_v1"] else "same"
        lines.append(
            f"- `{result['case_id']}` {result['chart']}: "
            f"v2 `{result['top_node_v2']}` / `{result['top_category_v2']}` "
            f"(v1 `{result['top_node_v1_counterfactual']}`, {changed})"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V50 Policy Anti-Overfit Review v1.")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = run_review(write_report=args.write_report)
    print(
        json.dumps(
            {
                "group": summary["group"],
                "total": summary["total"],
                "overfit_warning": summary["overfit_warning"],
                "category_counts_v2": summary["category_counts_v2"],
                "llm_used": summary["llm_used"],
                "brain_used": summary["brain_used"],
                "training_performed": summary["training_performed"],
                "weight_adjustment_performed": summary["weight_adjustment_performed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if summary["overfit_warning"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
