from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=10) as response:  # noqa: S310 - operator-provided local service URL.
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"non-object JSON response from {url}")
    return payload


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:  # noqa: S310 - operator-provided local service URL.
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError(f"non-object JSON response from {url}")
    return parsed


def _url(base_url: str, path: str, query: dict[str, Any] | None = None) -> str:
    target = base_url.rstrip("/") + path
    if query:
        target += "?" + urlencode(query)
    return target


def run_smoke(base_url: str, reading_id: str) -> dict[str, Any]:
    failures: list[str] = []
    health = _get_json(_url(base_url, "/api/v30/health"))
    if health.get("ok") is not True or health.get("package") != "v30":
        failures.append("health_contract_failed")

    created = _post_json(
        _url(base_url, "/api/v30/readings"),
        {
            "reading_id": reading_id,
            "locale": "zh",
            "target_year": 2030,
            "actor_id": "r2-live-user",
            "session_id": "r2-live-session",
            "birth_input": {
                "input_id": f"{reading_id}-input",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            },
        },
    )
    if created.get("status") != "ready" or not created.get("trace_id"):
        failures.append("create_reading_not_ready")

    user_view = _get_json(
        _url(
            base_url,
            f"/api/v30/readings/{reading_id}/view",
            {"role": "user", "locale": "zh", "client": "web"},
        )
    )
    user_surface = user_view.get("reading_surface", {}) if isinstance(user_view, dict) else {}
    user_contract = user_view.get("projection_contract", {}) if isinstance(user_view, dict) else {}
    next_question = user_surface.get("next_question", {}) if isinstance(user_surface, dict) else {}
    question_id = str(next_question.get("question_id") or "")
    if user_view.get("diagnostics"):
        failures.append("user_diagnostics_visible")
    if user_contract.get("version") != "v30.api_projection_contract.v1":
        failures.append("projection_contract_missing")
    if user_contract.get("leak_scan", {}).get("passed") is not True:
        failures.append("projection_leak_scan_failed")
    if user_surface.get("core_bazi_reading", {}).get("surface_type") != "core_bazi_calculation":
        failures.append("core_bazi_reading_missing")
    if not question_id:
        failures.append("visible_next_question_missing")

    admin_view = _get_json(
        _url(
            base_url,
            f"/api/v30/readings/{reading_id}/view",
            {"role": "admin", "locale": "zh", "client": "admin"},
        )
    )
    if not admin_view.get("diagnostics") or admin_view.get("projection_contract", {}).get("diagnostics_visible") is not True:
        failures.append("admin_diagnostics_missing")

    answer = _post_json(
        _url(base_url, f"/api/v30/readings/{reading_id}/questions/{question_id}/answer"),
        {
            "answer": "我主要想先看事业方向，近两年压力比较明显。",
            "role": "user",
            "locale": "zh",
            "client": "web",
            "outcome_status": "answered",
            "selected_option": "career:pressure",
            "confidence": 0.78,
            "feedback_tags": ["r2_live_api_smoke", "customer_loop"],
        },
    )
    answer_view = answer.get("view", {}) if isinstance(answer, dict) else {}
    answer_surface = answer_view.get("reading_surface", {}) if isinstance(answer_view, dict) else {}
    interaction_state = answer.get("interaction_state", {}) if isinstance(answer, dict) else {}
    if answer.get("accepted") is not True or answer.get("question_outcome_consumed") is not True:
        failures.append("answer_not_consumed")
    if not answer.get("next_question_id") or not answer.get("internal_next_question_id"):
        failures.append("answer_next_question_ids_missing")
    if interaction_state.get("version") != "v30.interaction_state.v1":
        failures.append("interaction_state_missing")
    if not answer_view.get("answer_panel"):
        failures.append("answer_panel_missing")
    if answer_surface.get("next_question", {}).get("question_id") == question_id:
        failures.append("visible_next_question_not_refreshed")

    history = _get_json(
        _url(
            base_url,
            "/api/v30/readings/history",
            {
                "actor_id": "r2-live-user",
                "session_id": "r2-live-session",
                "role": "user",
                "locale": "zh",
                "client": "web",
                "limit": 10,
            },
        )
    )
    admin_history = _get_json(
        _url(
            base_url,
            "/api/v30/readings/history",
            {
                "actor_id": "r2-live-user",
                "session_id": "r2-live-session",
                "role": "admin",
                "locale": "zh",
                "client": "admin",
                "limit": 10,
            },
        )
    )
    history_item = history.get("items", [{}])[0] if history.get("items") else {}
    admin_history_item = admin_history.get("items", [{}])[0] if admin_history.get("items") else {}
    owner_filter = history.get("owner_filter", {}) if isinstance(history.get("owner_filter"), dict) else {}
    visibility_contract = history.get("visibility_contract", {}) if isinstance(history.get("visibility_contract"), dict) else {}
    admin_owner_filter = admin_history.get("owner_filter", {}) if isinstance(admin_history.get("owner_filter"), dict) else {}
    admin_visibility_contract = admin_history.get("visibility_contract", {}) if isinstance(admin_history.get("visibility_contract"), dict) else {}
    admin_history_diagnostics = admin_history.get("diagnostics", {}) if isinstance(admin_history.get("diagnostics"), dict) else {}
    if history.get("version") != "v30.reading_history_projection.v1" or history.get("count", 0) < 1:
        failures.append("history_user_projection_missing")
    if owner_filter.get("version") != "v30.reading_history_ownership.v1":
        failures.append("history_owner_filter_missing")
    if owner_filter.get("scope") != "actor_and_session":
        failures.append("history_owner_filter_scope_not_exact")
    if "actor_id" in owner_filter or "session_id" in owner_filter:
        failures.append("history_user_owner_ids_visible")
    if visibility_contract.get("guest_user_internal_fields_hidden") is not True or history.get("diagnostics"):
        failures.append("history_user_visibility_contract_failed")
    if "actor_context" in history_item or "internal_next_question_id" in history_item:
        failures.append("history_user_internal_fields_visible")
    if history_item.get("owner_match", {}).get("diagnostic_ids_visible") is not False:
        failures.append("history_user_owner_match_not_sanitized")
    if admin_owner_filter.get("actor_id") != "r2-live-user" or admin_owner_filter.get("session_id") != "r2-live-session":
        failures.append("history_admin_owner_filter_ids_missing")
    if admin_visibility_contract.get("diagnostic_role") is not True or not admin_history_diagnostics.get("trace_ids"):
        failures.append("history_admin_visibility_contract_failed")
    if not admin_history_item.get("actor_context") or not admin_history_item.get("internal_next_question_id"):
        failures.append("history_admin_diagnostics_missing")

    return {
        "version": "v30.production_api_smoke.v1",
        "base_url": base_url.rstrip("/"),
        "reading_id": reading_id,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "summary": {
            "health_ok": health.get("ok") is True,
            "created_status": created.get("status", ""),
            "trace_id": created.get("trace_id", ""),
            "projection_contract_version": user_contract.get("version", ""),
            "answer_accepted": answer.get("accepted") is True,
            "answer_panel_present": bool(answer_view.get("answer_panel")),
            "interaction_state_version": interaction_state.get("version", ""),
            "history_count": history.get("count", 0),
            "history_owner_scope": owner_filter.get("scope", ""),
            "history_user_owner_ids_hidden": "actor_id" not in owner_filter and "session_id" not in owner_filter,
            "history_user_diagnostics_hidden": history.get("diagnostics") == {},
            "admin_history_diagnostics_visible": bool(admin_history_item.get("actor_context"))
            and bool(admin_history_item.get("internal_next_question_id")),
        },
        "boundary": "live_api_smoke_validates_served_contract_not_chart_fact_mutation",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 production API smoke against a live service port.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9030")
    parser.add_argument("--reading-id", default="r2-live-api-smoke")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_smoke(args.base_url, args.reading_id)
    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
        result = {
            "version": "v30.production_api_smoke.v1",
            "base_url": args.base_url.rstrip("/"),
            "reading_id": args.reading_id,
            "status": "failed",
            "failures": [f"live_api_smoke_exception:{type(exc).__name__}:{exc}"],
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {result['status']} base_url={result['base_url']} reading_id={result['reading_id']}")
        for failure in result.get("failures", []):
            print(f"- {failure}")
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
