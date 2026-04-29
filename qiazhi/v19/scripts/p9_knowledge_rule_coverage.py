#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict


DEFAULT_BIRTH_INPUT = {
    "year": 1990,
    "month": 11,
    "day": 13,
    "hour": 12,
    "minute": 0,
    "gender": "male",
    "calendar_type": "solar",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Review V19 P9 knowledge -> Rule DB -> structural signal coverage.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9019", help="V19 base URL.")
    parser.add_argument("--role", default="admin", help="Role query fallback.")
    parser.add_argument("--selected-year", type=int, default=2026, help="Flow year used as sample time context.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    payload = {
        "birth_input": DEFAULT_BIRTH_INPUT,
        "selected_year": args.selected_year,
        "message": "P9 knowledge rule signal coverage review",
    }
    response = _post_json(f"{args.base_url.rstrip('/')}/api/lab/knowledge-rule-signal-coverage?role={args.role}", payload)
    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(response)
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    report = data.get("knowledge_rule_signal_coverage") if isinstance(data.get("knowledge_rule_signal_coverage"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return 0 if response.get("ok") is not False and int(summary.get("eligible_draft_count") or 0) > 0 else 1


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
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


def _print_text(response: Dict[str, Any]) -> None:
    if response.get("ok") is False:
        print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
        return
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    report = data.get("knowledge_rule_signal_coverage") if isinstance(data.get("knowledge_rule_signal_coverage"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    by_status = summary.get("by_status") if isinstance(summary.get("by_status"), dict) else {}
    print("V19 P9 knowledge -> Rule DB -> Structural Signal coverage")
    print(
        "summary: "
        f"drafts={summary.get('draft_count', 0)} · "
        f"eligible={summary.get('eligible_draft_count', 0)} · "
        f"rules={summary.get('rule_count', 0)} · "
        f"engine_ready={summary.get('engine_ready_eligible_count', 0)} · "
        f"sample_signals={summary.get('sample_signal_covered_count', 0)} · "
        f"gaps={summary.get('gap_count', 0)}"
    )
    if by_status:
        print("by_status: " + ", ".join(f"{key}={value}" for key, value in sorted(by_status.items())))
    gap_items = [item for item in report.get("items") or [] if item.get("gaps")]
    if gap_items:
        print("gaps:")
        for item in gap_items[:24]:
            print(
                f"- {item.get('knowledge_id')} · {item.get('status')} · "
                f"{', '.join(item.get('gaps') or [])} · rule={','.join(item.get('rule_ids') or []) or '-'}"
            )
    else:
        print("gaps: none")


if __name__ == "__main__":
    sys.exit(main())
