from __future__ import annotations

from typing import Any

from core.life_case import LifeCase
from core.mingli_agent import MingliCognitiveRecord


def case_summary(row: dict[str, Any]) -> dict[str, Any]:
    record = MingliCognitiveRecord.model_validate(row["record"])
    birth = row.get("birth_input", {})
    life_case = LifeCase.model_validate(row["life_case"]) if row.get("life_case") else None
    first_look = life_case.baseline_insight.claim if life_case else record.cognition.first_look
    return {
        "case_id": row["case_id"],
        "profile_id": row.get("profile_id"),
        "display_name": birth.get("name") or "命理档案",
        "pillars": [
            birth.get("year_pillar"),
            birth.get("month_pillar"),
            birth.get("day_pillar"),
            birth.get("hour_pillar"),
        ],
        "first_look": first_look,
        "revision_count": len(life_case.revisions) if life_case else len(record.revisions),
        "reliability_state": record.reliability_disposition,
        "life_case_status": life_case.status if life_case else "uncommitted",
        "case_version": life_case.case_version if life_case else "",
        "read_only": bool(
            life_case and (life_case.status != "active" or not life_case.chart_version.active)
        ),
    }


def is_current_cognitive_record(row: dict[str, Any]) -> bool:
    record = row.get("record") or {}
    if not isinstance(record, dict) or record.get("version") not in {
        "deepbazi.mingli_cognitive_record.v2",
        "deepbazi.mingli_cognitive_record.v3",
    }:
        return False
    review = record.get("review") or {}
    if review.get("gate_version") != "mingli_reliability_gate_v1":
        return False
    disposition = record.get("reliability_disposition") or review.get("disposition")
    life_case_payload = row.get("life_case")
    if isinstance(life_case_payload, dict):
        try:
            life_case = LifeCase.model_validate(life_case_payload)
        except Exception:  # noqa: BLE001 - malformed stored contract is not current.
            return False
        if life_case.status != "active" or not life_case.chart_version.active:
            return False
    if disposition in {"blocked", "competing"}:
        return True
    receipts = record.get("stage_receipts") if isinstance(record, dict) else None
    required_stages = {"pattern_hypothesis", "work_path_portrait", "prediction_probe"}
    if record.get("version") == "deepbazi.mingli_cognitive_record.v2":
        required_stages.update({"career_reasoning", "wealth_reasoning"})
    completed = {
        str(item.get("stage"))
        for item in (receipts or [])
        if isinstance(item, dict) and item.get("status") == "completed"
    }
    if "baseline_cognition" in completed:
        life_case = row.get("life_case") or {}
        baseline = life_case.get("baseline_insight") if isinstance(life_case, dict) else None
        return bool(isinstance(baseline, dict) and baseline.get("status") == "committed")
    return required_stages.issubset(completed)


def is_domain_eligible(row: dict[str, Any]) -> bool:
    if not is_current_cognitive_record(row):
        return False
    record = row.get("record") or {}
    review = record.get("review") or {}
    if record.get("reliability_disposition") != "reliable" or not review.get("commit_eligible"):
        return False
    life_case = row.get("life_case") or {}
    baseline = life_case.get("baseline_insight") if isinstance(life_case, dict) else None
    return bool(
        isinstance(baseline, dict)
        and baseline.get("status") == "committed"
        and life_case.get("status") == "active"
        and (life_case.get("chart_version") or {}).get("active") is True
    )


def is_historical_life_case(row: dict[str, Any]) -> bool:
    payload = row.get("life_case")
    if not isinstance(payload, dict):
        return False
    try:
        life_case = LifeCase.model_validate(payload)
    except Exception:  # noqa: BLE001 - malformed legacy rows are not formal history.
        return False
    return life_case.status in {"superseded", "archived"} or not life_case.chart_version.active
