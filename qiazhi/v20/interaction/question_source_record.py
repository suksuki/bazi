from __future__ import annotations

import hashlib
import json

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "question_source_ranking_ledger"
REPORT_VERSION = "v20.question_source_ranking_report.v1"


def analyze_question_source_ranking_report(
    *,
    input_id: str,
    source_role: str,
    question_source_ranking_report: dict[str, object],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    _validate_report(question_source_ranking_report)
    persistable = _persistable_report(question_source_ranking_report)
    source_hash = _source_hash(input_id, source_role, locale, json.dumps(persistable, ensure_ascii=False, sort_keys=True))
    return {
        "version": "v20.question_source_ranking_analysis.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "input_id": input_id,
        "question_count": persistable["question_count"],
        "source_path_count": persistable["source_path_count"],
        "missing_source_count": len(persistable["missing_source_keys"]),
        "top_source_key": persistable["rows"][0]["source_key"] if persistable["rows"] else "",
        "question_source_ranking_report": persistable,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_SOURCE_ANALYSIS_ONLY",
            "NO_RAW_USER_TEXT_PERSISTED",
            "NO_QUESTION_ORDER_MUTATION",
            "NO_RUNTIME_POLICY_WRITE",
        ],
    }


def record_question_source_ranking_report(
    *,
    input_id: str,
    source_role: str,
    question_source_ranking_report: dict[str, object],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_question_source_ranking_report(
        input_id=input_id,
        source_role=source_role,
        question_source_ranking_report=question_source_ranking_report,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(LEDGER_NAME, _persistable_payload(analysis))
    return {
        "version": "v20.question_source_ranking_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_QUESTION_SOURCE_RANKING",
            "NO_RUNTIME_RECOMMENDATION_MUTATION",
            "NO_USER_VISIBLE_RESULT_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "input_id": analysis["input_id"],
        "question_count": analysis["question_count"],
        "source_path_count": analysis["source_path_count"],
        "missing_source_count": analysis["missing_source_count"],
        "top_source_key": analysis["top_source_key"],
        "question_source_ranking_report": analysis["question_source_ranking_report"],
        "runtime_mutation": False,
        "guardrails": analysis["guardrails"],
    }


def _persistable_report(report: dict[str, object]) -> dict[str, object]:
    rows = []
    for row in report.get("rows", ()):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "rank": int(row.get("rank", 0) or 0),
                "question_key": str(row.get("question_key", "")),
                "domain": str(row.get("domain", "")),
                "question_strategy": str(row.get("question_strategy", "")),
                "source_key": str(row.get("source_key", "")),
                "source_graph_score": _float(row.get("source_graph_score", 0)),
                "question_score": _float(row.get("question_score", 0)),
                "arbitration_notes": [str(note) for note in row.get("arbitration_notes", ()) if str(note)]
                if isinstance(row.get("arbitration_notes", ()), (list, tuple))
                else [],
            }
        )
    return {
        "version": REPORT_VERSION,
        "status": str(report.get("status", "")),
        "question_count": int(report.get("question_count", 0) or 0),
        "source_path_count": int(report.get("source_path_count", 0) or 0),
        "missing_source_keys": [str(row) for row in report.get("missing_source_keys", ()) if str(row)]
        if isinstance(report.get("missing_source_keys", ()), (list, tuple))
        else [],
        "rows": rows,
        "runtime_mutation": False,
    }


def _validate_report(report: dict[str, object]) -> None:
    if not isinstance(report, dict):
        raise ValueError("question_source_ranking_report must be an object")
    if report.get("version") != REPORT_VERSION:
        raise ValueError(f"Unsupported question_source_ranking_report version: {report.get('version', '')}")
    if not isinstance(report.get("rows", ()), (list, tuple)):
        raise ValueError("question_source_ranking_report.rows must be a list")
    text = json.dumps(report, ensure_ascii=False, sort_keys=True)
    blocked = ("user_text", "feedback_text", "raw_feedback", "raw_private", "email", "phone")
    if any(token in text for token in blocked):
        raise ValueError("question_source_ranking_report contains raw text or private-field markers")


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"user", "analyst", "admin", "lab", "practitioner"}:
        raise ValueError(f"Unsupported question source source_role: {source_role}")


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]


def _float(value: object) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0
