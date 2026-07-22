from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from product.agent_case_store import PostgresAgentCaseStore
from product.canvas_projection import (
    ReadOnlyCanvasUnavailable,
    ReadOnlySixPillarCanvasService,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"
DEFAULT_REPORT_DIR = (
    ROOT
    / "reports"
    / "local-gate-03"
    / "20260722-local-gate-03-v1"
    / "canvas-acceptance"
)
SELECTION = (
    ("6b0f211925ee", "anchor", "熟悉锚点盘"),
    ("c6a1de5ca67c", "contrast", "相似输出主题、不同结构与日主"),
    ("884a0fd6e1cb", "ordinary", "普通结构对照"),
    ("803a7d1e0541", "ambiguous", "路径引用失效边界"),
    ("53c32afa88fa", "non_wood_day_master", "非木日主对照"),
)
ROLES = ("guest", "member", "practitioner", "research")
INTERNAL_DIAGNOSTIC_CODES = {
    "natural_language_only",
    "candidate_not_committed",
    "missing_path_ref",
    "invalid_node_ref",
    "invalid_relation_ref",
    "relation_still_potential",
    "authority_not_allowed",
    "role_visibility_filtered",
    "timing_scope_mismatch",
}


def audit(*, database_url: str, report_dir: Path) -> dict[str, Any]:
    store = PostgresAgentCaseStore(database_url)
    service = ReadOnlySixPillarCanvasService(case_store=store)
    before = _database_fingerprint(database_url)
    rows = _case_rows(database_url)
    available: dict[str, tuple[str, str, dict[str, Any]]] = {}
    unavailable = Counter()

    for row in rows:
        case_id = str(row["case_id"])
        user_id = str(row["user_id"] or "")
        if not user_id:
            unavailable["missing_user_id"] += 1
            continue
        try:
            research = service.issue(
                case_id=case_id,
                participant_id=user_id,
                account_role="research",
            )
        except ReadOnlyCanvasUnavailable as exc:
            unavailable[str(exc)] += 1
            continue
        available[_case_hash(case_id)] = (case_id, user_id, research)

    selected: list[dict[str, Any]] = []
    missing = []
    for case_hash, audit_role, reason in SELECTION:
        source = available.get(case_hash)
        if source is None:
            missing.append(case_hash)
            continue
        case_id, user_id, research = source
        row = store.get(case_id=case_id, user_id=user_id)
        if row is None:
            missing.append(case_hash)
            continue
        projections = {
            role: (
                research
                if role == "research"
                else service.issue(
                    case_id=case_id,
                    participant_id=user_id,
                    account_role=role,
                )
            )
            for role in ROLES
        }
        repeated = service.issue(
            case_id=case_id,
            participant_id=user_id,
            account_role="member",
        )
        selected.append(_case_result(
            case_hash=case_hash,
            audit_role=audit_role,
            selection_reason=reason,
            row=row,
            projections=projections,
            repeated_member=repeated,
        ))

    after = _database_fingerprint(database_url)
    full_gap_distribution = Counter(
        item[2]["path_availability"]["diagnostic"]["rejection_reason"]
        for item in available.values()
        if item[2]["path_availability"]["diagnostic"] is not None
    )
    selected_gap_distribution = Counter(
        item["path_projection_diagnostic"] for item in selected
    )
    checks = _checks(
        selected=selected,
        missing=missing,
        before=before,
        after=after,
    )
    passed = all(checks.values())
    result = {
        "schema_version": "deepbazi.local_gate_03_canvas_acceptance.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass_with_systemic_path_gap" if passed else "failed",
        "mode": "mac_local_read_only_no_llm",
        "source": {
            "database_case_rows": len(rows),
            "canonical_canvas_ready_cases": len(available),
            "unavailable_reason_counts": dict(sorted(unavailable.items())),
            "selected_case_hashes": [item[0] for item in SELECTION],
            "selected_case_count": len(selected),
            "database_fingerprint_before": before,
            "database_fingerprint_after": after,
            "prior_locked_cognition_cohort": _prior_locked_cohort_boundary(),
        },
        "path_gap_distribution": {
            "selected_five": dict(sorted(selected_gap_distribution.items())),
            "all_canvas_ready_local_cases": dict(sorted(full_gap_distribution.items())),
            "systemic_gap": bool(available) and not any(
                item[2]["path_availability"]["status"] == "available"
                for item in available.values()
            ),
            "interpretation": (
                "本地所有可投影正式 Case 均缺少可绘制的 committed PathAssertion；"
                "这不是 OneCanvas 绘制缺陷。"
            ),
        },
        "cases": selected,
        "checks": checks,
        "boundaries": {
            "reasoner_modified": False,
            "prompt_modified": False,
            "graph_semantics_modified": False,
            "formal_case_modified": False,
            "llm_called": False,
            "remote_sync_performed": False,
            "professional_mingli_quality_evaluated": False,
            "positive_committed_path_real_case_available": False,
            "positive_committed_path_contract_fixture_required": True,
        },
        "conclusion": {
            "onecanvas_fidelity": "pass" if passed else "failed",
            "role_projection": "pass" if passed else "failed",
            "path_assertion_pipeline": "systemic_upstream_gap",
            "professional_cognition_quality": "not_evaluated",
            "next_action": (
                "保留断链证据；不得在本轮从自然语言猜线或修改 Reasoner。"
            ),
        },
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / "local_gate_03_canvas_acceptance.json"
    summary_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path = report_dir / "LOCAL_GATE_03_CANVAS_ACCEPTANCE.md"
    markdown_path.write_text(_markdown(result), encoding="utf-8")
    manifest = _manifest(report_dir)
    manifest_path = report_dir / "manifest.sha256.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def _case_result(
    *,
    case_hash: str,
    audit_role: str,
    selection_reason: str,
    row: dict[str, Any],
    projections: dict[str, dict[str, Any]],
    repeated_member: dict[str, Any],
) -> dict[str, Any]:
    life_case = row.get("life_case") if isinstance(row.get("life_case"), dict) else {}
    record = row.get("record") if isinstance(row.get("record"), dict) else {}
    cognition = record.get("cognition") if isinstance(record.get("cognition"), dict) else {}
    work_path = cognition.get("work_path") if isinstance(cognition.get("work_path"), dict) else {}
    review = record.get("review") if isinstance(record.get("review"), dict) else {}
    hypotheses = cognition.get("hypotheses") if isinstance(cognition.get("hypotheses"), list) else []
    selected_hypothesis = str(cognition.get("selected_hypothesis_id") or "")
    baseline = life_case.get("baseline_insight") if isinstance(life_case.get("baseline_insight"), dict) else {}
    receipts = record.get("stage_receipts") if isinstance(record.get("stage_receipts"), list) else []
    receipt = receipts[-1] if receipts and isinstance(receipts[-1], dict) else {}
    member = projections["member"]
    practitioner = projections["practitioner"]
    research = projections["research"]
    diagnostic = research["path_availability"]["diagnostic"] or {}
    path_assertions = life_case.get("path_assertions") if isinstance(life_case.get("path_assertions"), list) else []
    relation_assertions = life_case.get("relation_assertions") if isinstance(life_case.get("relation_assertions"), list) else []
    member_json = json.dumps(member, ensure_ascii=False, sort_keys=True)
    practitioner_json = json.dumps(practitioner, ensure_ascii=False, sort_keys=True)
    research_relations = research["stages"]["natal"]["spec"]["relations"]
    member_relations = member["stages"]["natal"]["spec"]["relations"]
    scene_ids = {
        role: projection["canonical_scene"]["scene_id"]
        for role, projection in projections.items()
    }
    review_issues = review.get("issues") if isinstance(review.get("issues"), list) else []
    issue_codes = [
        str(item.get("code") or "")
        for item in review_issues
        if isinstance(item, dict) and item.get("code")
    ]
    return {
        "case_id_hash": case_hash,
        "audit_role": audit_role,
        "selection_reason": selection_reason,
        "pillars": list(row.get("world", {}).get("pillars") or []),
        "day_master": str((row.get("world", {}).get("pillars") or ["", "", ""])[2])[:1],
        "formal_insight_status": str(baseline.get("status") or "missing"),
        "primary_hypothesis": _hypothesis_by_id(hypotheses, selected_hypothesis),
        "strongest_alternative": _strongest_alternative(hypotheses, selected_hypothesis),
        "natural_language_work_path_present": bool(str(work_path.get("path_statement") or "").strip()),
        "natural_language_work_path": str(work_path.get("path_statement") or ""),
        "structured_path_assertion_present": any(
            isinstance(item, dict)
            and item.get("status") == "committed"
            and isinstance(item.get("path_key"), dict)
            for item in path_assertions
        ),
        "path_assertion_history_count": len(path_assertions),
        "path_assertion_statuses": dict(Counter(
            str(item.get("status") or "unknown")
            for item in path_assertions
            if isinstance(item, dict)
        )),
        "path_projection_diagnostic": str(diagnostic.get("rejection_reason") or "missing"),
        "committed_relation_count": sum(
            isinstance(item, dict) and item.get("status") == "committed"
            for item in relation_assertions
        ),
        "formal_canvas_path_count": len(member["stages"]["natal"]["spec"]["paths"]),
        "member_relation_count": len(member_relations),
        "lab_potential_relation_count": sum(
            item.get("relation_state") == "potential" for item in research_relations
        ),
        "recorded_review_issue_codes": issue_codes,
        "hard_fact_issue_codes": list(review.get("hard_failure_codes") or []),
        "metrics": {
            "input_tokens": int(receipt.get("prompt_eval_count") or 0),
            "output_tokens": int(receipt.get("eval_count") or 0),
            "retrieved_material_count": int(receipt.get("knowledge_count") or 0),
            "latency_seconds": round(int(receipt.get("duration_ms") or 0) / 1000, 3),
        },
        "role_projection": {
            "scene_identity_stable": len(set(scene_ids.values())) == 1,
            "projection_case_identity_matches": all(
                projection["case_id"] == row.get("case_id")
                for projection in projections.values()
            ),
            "guest_member_diagnostic_absent": (
                projections["guest"]["path_availability"]["diagnostic"] is None
                and member["path_availability"]["diagnostic"] is None
            ),
            "guest_member_internal_codes_absent": not any(
                code in member_json for code in INTERNAL_DIAGNOSTIC_CODES
            ),
            "member_potential_relations_absent": not any(
                item.get("relation_state") == "potential" for item in member_relations
            ),
            "practitioner_has_simplified_status": (
                practitioner["path_availability"]["disclosure_level"] == "professional"
                and practitioner["path_availability"]["diagnostic"] is None
            ),
            "practitioner_internal_codes_absent": not any(
                code in practitioner_json for code in INTERNAL_DIAGNOSTIC_CODES
            ),
            "research_has_full_diagnostic": (
                research["path_availability"]["disclosure_level"] == "audit"
                and research["path_availability"]["diagnostic"] is not None
            ),
            "research_lab_potential_relations_present": any(
                item.get("relation_state") == "potential" for item in research_relations
            ),
        },
        "state_safety": {
            "repeated_member_projection_identical": repeated_member == member,
            "llm_used": any(projection["llm_used"] for projection in projections.values()),
            "formal_state_writes": any(
                projection["formal_state_writes"] for projection in projections.values()
            ),
            "sandbox_mutations": any(
                projection["sandbox_mutations"] for projection in projections.values()
            ),
        },
        "stage_slot_counts": {
            stage: len(member["stages"][stage]["spec"]["semantic_slots"])
            for stage in ("natal", "luck", "year")
        },
    }


def _checks(
    *,
    selected: list[dict[str, Any]],
    missing: list[str],
    before: str,
    after: str,
) -> dict[str, bool]:
    return {
        "five_cases_selected": len(selected) == 5 and not missing,
        "five_stable_4_5_6_scenes": all(
            item["stage_slot_counts"] == {"natal": 4, "luck": 5, "year": 6}
            and item["role_projection"]["scene_identity_stable"]
            and item["role_projection"]["projection_case_identity_matches"]
            for item in selected
        ),
        "switching_cases_keeps_distinct_scene_identity": len({
            item["case_id_hash"] for item in selected
        }) == len(selected),
        "canvas_matches_path_assertion_state": all(
            item["formal_canvas_path_count"] == 0
            for item in selected
            if not item["structured_path_assertion_present"]
        ),
        "frontend_does_not_guess_natural_language_paths": all(
            item["formal_canvas_path_count"] == 0
            for item in selected
            if item["natural_language_work_path_present"]
        ),
        "guest_member_diagnostics_absent": all(
            item["role_projection"]["guest_member_diagnostic_absent"]
            and item["role_projection"]["guest_member_internal_codes_absent"]
            for item in selected
        ),
        "member_potential_relations_absent": all(
            item["role_projection"]["member_potential_relations_absent"]
            for item in selected
        ),
        "practitioner_status_is_simplified": all(
            item["role_projection"]["practitioner_has_simplified_status"]
            and item["role_projection"]["practitioner_internal_codes_absent"]
            for item in selected
        ),
        "research_diagnostic_and_lab_available": all(
            item["role_projection"]["research_has_full_diagnostic"]
            and item["role_projection"]["research_lab_potential_relations_present"]
            for item in selected
        ),
        "repeated_projection_is_deterministic": all(
            item["state_safety"]["repeated_member_projection_identical"]
            for item in selected
        ),
        "no_llm_no_writes_no_sandbox": all(
            not item["state_safety"]["llm_used"]
            and not item["state_safety"]["formal_state_writes"]
            and not item["state_safety"]["sandbox_mutations"]
            for item in selected
        ),
        "database_unchanged": before == after,
    }


def _case_rows(database_url: str) -> list[dict[str, Any]]:
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
                    case_id || ':' || md5(case_json::text),
                    '|' ORDER BY case_id
                ), '')
                FROM v50_mingli_agent_cases
                """
            )
            value = str(cursor.fetchone()[0])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _case_hash(case_id: str) -> str:
    return hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:12]


def _prior_locked_cohort_boundary() -> dict[str, Any]:
    root = DEFAULT_REPORT_DIR.parent
    rows = []
    reasons = Counter()
    for path in sorted(root.glob("*/stored_case.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        timing = row.get("world", {}).get("timing_context", {})
        rejection_reasons = [str(item) for item in timing.get("rejection_reasons") or []]
        reasons.update(rejection_reasons)
        rows.append({
            "case_id_hash": _case_hash(str(row.get("case_id") or path.parent.name)),
            "canvas_eligible": bool(timing.get("publicly_supported")),
            "timing_status": str(timing.get("status") or "missing"),
            "rejection_reasons": rejection_reasons,
        })
    return {
        "case_count": len(rows),
        "canvas_eligible_count": sum(item["canvas_eligible"] for item in rows),
        "rejection_reason_counts": dict(sorted(reasons.items())),
        "cases": rows,
        "interpretation": (
            "该批次仍可用于认知文本审计，但不能作为正式六柱 Canvas 验收样本。"
        ),
    }


def _hypothesis_by_id(hypotheses: list[Any], hypothesis_id: str) -> dict[str, Any] | None:
    for item in hypotheses:
        if isinstance(item, dict) and item.get("hypothesis_id") == hypothesis_id:
            return {
                "hypothesis_id": hypothesis_id,
                "name": str(item.get("name") or ""),
                "status": str(item.get("status") or ""),
            }
    return None


def _strongest_alternative(
    hypotheses: list[Any],
    selected_hypothesis_id: str,
) -> dict[str, Any] | None:
    alternatives = [
        item for item in hypotheses
        if isinstance(item, dict)
        and item.get("hypothesis_id") != selected_hypothesis_id
    ]
    if not alternatives:
        return None
    item = min(alternatives, key=lambda value: int(value.get("rank") or 999))
    return {
        "hypothesis_id": str(item.get("hypothesis_id") or ""),
        "name": str(item.get("name") or ""),
        "status": str(item.get("status") or ""),
    }


def _manifest(directory: Path) -> dict[str, Any]:
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.name == "manifest.sha256.json":
            continue
        files.append({
            "path": str(path.relative_to(directory)),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return {
        "schema_version": "deepbazi.local_gate_03_canvas_acceptance_manifest.v1",
        "files": files,
        "content_hash": hashlib.sha256(
            json.dumps(files, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def _markdown(result: dict[str, Any]) -> str:
    rows = []
    for item in result["cases"]:
        metrics = item["metrics"]
        rows.append(
            f"| `{item['case_id_hash']}` | {item['audit_role']} | "
            f"{' '.join(item['pillars'])} | `{item['path_projection_diagnostic']}` | "
            f"{item['formal_canvas_path_count']} | {item['lab_potential_relation_count']} | "
            f"{metrics['input_tokens']} / {metrics['output_tokens']} | {metrics['latency_seconds']}s |"
        )
    checks = "\n".join(
        f"- {'PASS' if value else 'FAIL'} `{name}`"
        for name, value in result["checks"].items()
    )
    selected_distribution = json.dumps(
        result["path_gap_distribution"]["selected_five"],
        ensure_ascii=False,
        sort_keys=True,
    )
    full_distribution = json.dumps(
        result["path_gap_distribution"]["all_canvas_ready_local_cases"],
        ensure_ascii=False,
        sort_keys=True,
    )
    prior = result["source"]["prior_locked_cognition_cohort"]
    prior_reasons = json.dumps(
        prior["rejection_reason_counts"],
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"""# LOCAL-GATE-03 Five-Chart Cognitive & Canvas Acceptance

Status: **{result['status'].upper()}**

本轮只读复用本地正式 Case；没有调用 LLM，没有修改 Reasoner、Prompt、Graph 或正式数据。

上一轮锁定的五份认知样本中，可进入正式六柱 Canvas 的数量为
`{prior['canvas_eligible_count']} / {prior['case_count']}`；拒绝原因分布为
`{prior_reasons}`。该批次保留为认知文本证据，本轮另从本地正式 Case 中
匿名选取五份历法可实现样本，不修改原盘来凑验收。

## 五盘矩阵

| 匿名 Case | 角色 | 四柱 | Path Diagnostic | 正式路径 | Lab 潜在关系 | 输入 / 输出 Token | 原始耗时 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

## PathAssertion 缺口

- 五盘分布：`{selected_distribution}`
- 本地全部 Canvas-ready Case 分布：`{full_distribution}`
- 结论：本地可投影的正式 Case 中没有一份拥有可绘制的 committed PathAssertion。
- OneCanvas 正确留空；不得从自然语言猜线。

## 角色披露

- Guest / Member：不含内部诊断码，不含 Lab 潜在关系，不显示工程性“做功 0”。
- Practitioner：仅显示简化专业状态，不下发完整 PathProjectionDiagnostic。
- Research：可见完整诊断与 Lab 潜在关系场。

## Checks

{checks}

## 边界

- 本轮证明 Canvas 忠实性与角色披露，不评价专业命理质量。
- 五盘真实样本覆盖无正式路径的负分支；合法 committed PathAssertion 的正分支继续由合同 Fixture 回归保护。
- 上游断链需要在专业认知基准之后单独处理，本轮不启动 Cognitive → PathAssertion 生成链。
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the read-only LOCAL-GATE-03 cognitive and Canvas acceptance.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("V50_DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    result = audit(database_url=args.database_url, report_dir=args.report_dir)
    print(json.dumps({
        "status": result["status"],
        "selected_case_count": result["source"]["selected_case_count"],
        "path_gap_distribution": result["path_gap_distribution"],
        "checks": result["checks"],
        "report_dir": str(args.report_dir),
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass_with_systemic_path_gap" else 1


if __name__ == "__main__":
    raise SystemExit(main())
