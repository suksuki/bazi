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
    parser = argparse.ArgumentParser(description="Review V19 P9 Rule DB structural-rule signals.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9019", help="V19 base URL.")
    parser.add_argument("--role", default="admin", help="Role query fallback.")
    parser.add_argument("--selected-year", type=int, default=2026, help="Flow year used as time context.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    payload = {"birth_input": DEFAULT_BIRTH_INPUT, "selected_year": args.selected_year, "message": "P9 structural rule signal review"}
    response = _post_json(f"{args.base_url.rstrip('/')}/api/lab/structural-rule-signals?role={args.role}", payload)
    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(response)
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    report = data.get("structural_rule_signals") if isinstance(data.get("structural_rule_signals"), dict) else {}
    return 0 if response.get("ok") is not False and int(report.get("count") or 0) > 0 else 1


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
    report = data.get("structural_rule_signals") if isinstance(data.get("structural_rule_signals"), dict) else {}
    print("V19 P9 structural rule signals")
    print(f"signals: {report.get('count', 0)} · version: {report.get('version', '-')}")
    facts = report.get("facts_summary") if isinstance(report.get("facts_summary"), dict) else {}
    if facts:
        print("facts: " + ", ".join(f"{key}={value}" for key, value in facts.items()))
    for item in (report.get("signals") or [])[:20]:
        observed = ", ".join(str(x) for x in item.get("observed") or []) or "-"
        refs = ", ".join(str(x) for x in item.get("fact_refs") or []) or "-"
        print(f"- {item.get('signal_id')} · {item.get('category')} · {item.get('layer')} · score {item.get('score')}")
        print(f"  observed: {observed}")
        print(f"  refs: {refs}")
        print(f"  scope: {item.get('answer_scope') or '-'}")


if __name__ == "__main__":
    sys.exit(main())
