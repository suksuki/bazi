#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Read V19 guided-question answer quality report.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9019", help="V19 base URL.")
    parser.add_argument("--role", default="admin", help="Role query fallback.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/api/lab/guided-question-answer-quality?role={args.role}"
    report = _get_json(url)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    by_status = summary.get("by_status") if isinstance(summary.get("by_status"), dict) else {}
    return 1 if int(by_status.get("fail") or 0) > 0 else 0


def _get_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
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


def _print_text_report(report: Dict[str, Any]) -> None:
    if report.get("ok") is False:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    by_status = summary.get("by_status") if isinstance(summary.get("by_status"), dict) else {}
    risk_flags = summary.get("risk_flags") if isinstance(summary.get("risk_flags"), list) else []
    print("V19 P7 answer quality report")
    print(f"records: {report.get('count', 0)}")
    print("status: " + ", ".join(f"{key}={value}" for key, value in sorted(by_status.items())) if by_status else "status: none")
    if risk_flags:
        print("risk flags:")
        for item in risk_flags[:12]:
            print(f"  - {item.get('key')}: {item.get('count')}")
    items = [item for item in report.get("items") or [] if item.get("status") != "pass"]
    if items:
        print("items needing review:")
        for item in items[:20]:
            flags = ", ".join(str(flag) for flag in item.get("risk_flags") or []) or "-"
            print(f"  - {item.get('status')} {item.get('question_key') or '-'} · {item.get('source_type')} · {flags}")
            preview = str(item.get("text_preview") or "").strip()
            if preview:
                print(f"    {preview[:180]}")
    else:
        print("items needing review: none")
    recs = report.get("recommendations") or []
    if recs:
        print("recommendations:")
        for rec in recs:
            print(f"  - {rec}")


if __name__ == "__main__":
    sys.exit(main())
