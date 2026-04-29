#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List


CORE_QUESTIONS: List[Dict[str, str]] = [
    {"key": "q_structure_overview", "message": "如果只看结构，这张命盘先呈现哪些特征？"},
    {"key": "q_day_master_month_anchor", "message": "这张命盘先看日主和月令，能读出什么结构基点？"},
    {"key": "q_month_command_anchor", "message": "月令在这张命盘里先提供了什么结构背景？"},
    {"key": "q_hidden_stem_role", "message": "藏干在这张命盘里只是补充信息，还是会影响结构理解？"},
    {"key": "q_ten_god_metadata", "message": "十神标签在这里为什么只是关系元数据，而不是断语？"},
    {"key": "q_element_flow_metadata", "message": "五行生克在这里应该怎样只按结构关系阅读？"},
    {"key": "q_branch_relation_detail", "message": "当前看得到的冲合关系，分别发生在本命还是时间背景？"},
    {"key": "q_combination_context", "message": "如果出现合或六合关系，它在这里只表示什么结构连接？"},
    {"key": "q_three_harmony_context", "message": "如果出现三合结构，它在这里只表示什么结构连接？"},
    {"key": "q_vault_structure", "message": "这张命盘里的墓库结构，应该如何只按结构层阅读？"},
    {"key": "q_income_stability", "message": "我的收入稳定性结构如何？"},
    {"key": "q_income_factors", "message": "当前结构中哪些因素影响收入稳定？"},
    {"key": "q_income_path_structure", "message": "如果只按结构看，收入路径是被哪些信号组织起来的？"},
    {"key": "q_signal_combination", "message": "这个结果主要由哪几个结构信号共同形成？"},
    {"key": "q_time_context", "message": "这个流年只作为时间背景，会触发哪些结构关系？"},
    {"key": "q_time_context_boundary", "message": "哪些结构关系只是背景，不应该直接理解成预测？"},
    {"key": "q_luck_flow_layers", "message": "大运和流年在这里分别属于哪一层结构？"},
    {"key": "q_time_vs_natal_relation", "message": "大运、流年和本命发生关系时，哪些只算背景，哪些才算本命结构？"},
    {"key": "q_time_not_inference", "message": "为什么当前时间结构不直接改变收入稳定性结果？"},
    {"key": "q_read_result_not_fortune", "message": "我应该如何阅读这个结果，而不是把它当成断语？"},
    {"key": "follow_rule_basis", "message": "查看这条判断的规则依据"},
]


DEFAULT_BIRTH_INPUT = {
    "year": 1990,
    "month": 11,
    "day": 13,
    "hour": 12,
    "minute": 0,
    "gender": "male",
    "calendar_type": "solar",
}


BAD_TEXT_MARKERS = [
    "answer_empty",
    "GUIDED_ANSWER",
    "DETERMINISTIC_RESULT_CARD",
    "rule_id",
    "signal_id",
    "question_basis",
    "source_signal_id",
    "income_stability，也不会生成预测",
    "不会改变 income_stability",
]

FORBIDDEN_PREDICTION_TERMS = [
    "一定",
    "必然",
    "发财",
    "破财",
    "今年会",
    "明年会",
    "好运",
    "坏运",
    "财运很好",
    "财运很差",
    "婚姻会",
    "健康会",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V19 guided-question audit matrix against a running server.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9019", help="V19 base URL.")
    parser.add_argument("--role", default="admin", help="Role query fallback.")
    parser.add_argument("--selected-year", type=int, default=2026, help="Flow year used as time context.")
    parser.add_argument("--save", action="store_true", help="Ask audit endpoint to save each audit record.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    results: List[Dict[str, Any]] = []
    for item in CORE_QUESTIONS:
        payload = {
            "save": bool(args.save),
            "birth_input": DEFAULT_BIRTH_INPUT,
            "selected_year": args.selected_year,
            "selected_question_key": item["key"],
            "message": item["message"],
        }
        response = _post_json(f"{args.base_url.rstrip('/')}/api/lab/guided-question-audit?role={args.role}", payload)
        results.append(_judge(item, response))

    failed = [row for row in results if row["status"] != "pass"]
    report = {
        "ok": not failed,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "items": results,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    return 0 if not failed else 1


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(raw)
        except Exception:
            parsed = raw
        return {"ok": False, "http_status": exc.code, "error": parsed}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _judge(question: Dict[str, str], response: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[str] = []
    failures: List[str] = []
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    if response.get("ok") is False:
        failures.append("endpoint_failed")
    contract = data.get("question_contract") if isinstance(data.get("question_contract"), dict) else {}
    intent = data.get("intent") if isinstance(data.get("intent"), dict) else {}
    retrieved = data.get("retrieved_facts") if isinstance(data.get("retrieved_facts"), dict) else {}
    observed = data.get("observed_facts") if isinstance(data.get("observed_facts"), dict) else {}
    composed = data.get("composed_text")
    text = _extract_text(composed)
    audit = data.get("audit") if isinstance(data.get("audit"), dict) else {}
    audit_checks = audit.get("checks") if isinstance(audit.get("checks"), list) else []

    _require(bool(contract), "contract_present", checks, failures)
    _require(str(contract.get("key") or question["key"]) == question["key"], "contract_key_matches", checks, failures)
    _require(bool(intent), "intent_present", checks, failures)
    _require(intent.get("supported") is not False, "intent_supported", checks, failures)
    _require(bool(retrieved), "retrieved_facts_present", checks, failures)
    _require(bool(observed), "observed_facts_present", checks, failures)
    _require(bool(text.strip()), "composed_text_present", checks, failures)
    _require(not any(marker in text for marker in BAD_TEXT_MARKERS), "no_internal_or_empty_text_markers", checks, failures)
    _require(not any(term in text for term in FORBIDDEN_PREDICTION_TERMS), "no_prediction_terms", checks, failures)
    _require(not _looks_truncated_text(text), "answer_not_truncated", checks, failures)
    if audit_checks:
        failed_audit = [
            str(row.get("name") or row.get("check") or "unknown")
            for row in audit_checks
            if isinstance(row, dict) and (row.get("passed") is False or row.get("ok") is False)
        ]
        if failed_audit:
            failures.append("audit_checks_failed:" + ",".join(failed_audit))
        else:
            checks.append("audit_checks_passed")

    return {
        "key": question["key"],
        "message": question["message"],
        "status": "fail" if failures else "pass",
        "checks": checks,
        "failures": failures,
        "answer_kind": intent.get("answer_kind") or data.get("answer_kind") or "",
        "text_preview": " ".join(text.split())[:160],
    }


def _require(ok: bool, name: str, checks: List[str], failures: List[str]) -> None:
    if ok:
        checks.append(name)
    else:
        failures.append(name)


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("zh") or value.get("text") or "")
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return ""


def _looks_truncated_text(text: str) -> bool:
    clean = str(text or "").strip()
    if len(clean) < 24:
        return False
    if clean.count("“") != clean.count("”"):
        return True
    if clean.count("‘") != clean.count("’"):
        return True
    if clean.count("（") != clean.count("）"):
        return True
    if clean.count("(") != clean.count(")"):
        return True
    if clean.endswith(("，", "、", "：", "；", ",", ":", ";", "的", "和", "与", "或", "而", "以及", "因为", "所以", "但是", "并且", "同时", "其中", "例如", "比如", "包括", "位于", "出现于")):
        return True
    if len(clean) >= 120 and clean[-1] not in "。！？.!?）】”’」』":
        return True
    return False


def _print_text_report(report: Dict[str, Any]) -> None:
    print(f"V19 guided question audit matrix: {report['passed']}/{report['total']} passed")
    for row in report["items"]:
        mark = "PASS" if row["status"] == "pass" else "FAIL"
        print(f"{mark} {row['key']} · {row.get('answer_kind') or '-'}")
        if row["status"] != "pass":
            print(f"  failures: {', '.join(row['failures'])}")
        if row.get("text_preview"):
            print(f"  answer: {row['text_preview']}")


if __name__ == "__main__":
    sys.exit(main())
