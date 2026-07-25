from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from core.life_domains import LifeDomain


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the live LLM life-domain matrix against a persisted case.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8053")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--email", default=os.getenv("V50_VALIDATION_ADMIN_EMAIL", "jerrydidi@gmail.com"))
    parser.add_argument("--password", default=os.getenv("V50_VALIDATION_ADMIN_PASSWORD", ""))
    parser.add_argument("--output-dir", default="reports/life-domain-live-matrix-v1")
    parser.add_argument("--domains", default="", help="Optional comma-separated subset for a remediation run.")
    args = parser.parse_args()
    if not args.password:
        raise SystemExit("V50_VALIDATION_ADMIN_PASSWORD is required")

    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    _post_json(opener, f"{args.base_url}/api/v50/product/auth/login", {"email": args.email, "password": args.password})
    results: list[dict[str, object]] = []
    requested = {
        item.strip()
        for item in args.domains.split(",")
        if item.strip()
    }
    for domain in LifeDomain:
        if domain is LifeDomain.WHOLE_CHART:
            continue
        if requested and domain.value not in requested:
            continue
        started = time.perf_counter()
        try:
            payload = _post_json(
                opener,
                f"{args.base_url}/api/v50/agent/cases/{args.case_id}/domains/{domain.value}",
                {"active_mode": "practitioner", "user_question": ""},
                timeout=360,
            )
            exploration = payload["reading"]["domain_explorations"][domain.value]
            reading = exploration["reading"]
            result = {
                "domain": domain.value,
                "status": "passed",
                "cache_hit": bool(payload.get("cache_hit")),
                "latency_seconds": round(time.perf_counter() - started, 3),
                "review_passed": exploration.get("review", {}).get("passed"),
                "traceability": exploration.get("review", {}).get("fact_traceability_rate"),
                "causal_step_count": len(reading.get("causal_chain") or []),
                "assertion_count": len(reading.get("assertions") or []),
                "has_domain_probe": bool(reading.get("next_probe")),
                "focused_palaces": exploration.get("context_manifest", {}).get("included_ziwei_palaces", []),
                "repaired": exploration.get("review", {}).get("repaired"),
                "core_question": reading.get("core_question", ""),
                "redline_violations": [],
            }
        except (HTTPError, URLError, KeyError, ValueError, json.JSONDecodeError) as exc:
            detail = _error_detail(exc)
            result = {
                "domain": domain.value,
                "status": "failed",
                "latency_seconds": round(time.perf_counter() - started, 3),
                "error": detail,
                "redline_violations": [],
            }
        results.append(result)
        print(json.dumps({"domain": domain.value, "status": result["status"], "latency_seconds": result["latency_seconds"]}, ensure_ascii=False), flush=True)

    failed = [item for item in results if item["status"] != "passed"]
    invalid = [
        item for item in results
        if item["status"] == "passed"
        and (
            item.get("review_passed") is not True
            or item.get("causal_step_count") != 4
            or int(item.get("assertion_count") or 0) < 2
            or item.get("has_domain_probe") is not True
        )
    ]
    status = "passed" if not failed and not invalid else "partial"
    report = {
        "run_name": "V50 Live Life Domain Matrix v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "case_id": args.case_id,
        "model_judgment_role": "llm_cognitive_reasoner",
        "domains_total": len(results),
        "domains_passed": len(results) - len(failed),
        "domains_failed": len(failed),
        "invalid_passes": len(invalid),
        "results": results,
        "boundaries": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "global_policy_promoted": False,
            "llm_used": True,
            "case_data_collection_only": True,
        },
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "life_domain_live_matrix_v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# V50 Live Life Domain Matrix v1",
        "",
        f"- Status: `{status}`",
        f"- Case: `{args.case_id}`",
        f"- Passed: `{report['domains_passed']}/{report['domains_total']}`",
        f"- Invalid passes: `{report['invalid_passes']}`",
        "",
        "## Observed Data",
        "",
        "| Domain | Status | Cache | Latency | Chain | Assertions | Probe | Traceability | Focused Ziwei |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for item in results:
        lines.append(
            f"| `{item['domain']}` | `{item['status']}` | {item.get('cache_hit', '-')} | {item['latency_seconds']}s | "
            f"{item.get('causal_step_count', '-')} | {item.get('assertion_count', '-')} | "
            f"{item.get('has_domain_probe', '-')} | {item.get('traceability', '-')} | "
            f"{', '.join(item.get('focused_palaces', [])) or '-'} |"
        )
        if item.get("error"):
            lines.append(f"\nFailure `{item['domain']}`: `{item['error']}`\n")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A pass means the domain owns a reviewed, evidence-linked, four-step causal reading with at least two falsifiable assertions and its own domain Probe. `Cache=True` means this run restored a previously live-generated result; first-generation and remediation latency remain in the phase reports. It does not prove the Mingli theory is true or the user experience is complete.",
        "",
        "## Boundaries",
        "",
        "```yaml",
        *[f"{key}: {str(value).lower()}" for key, value in report["boundaries"].items()],
        "```",
    ])
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if status == "passed" else 2


def _post_json(opener, url: str, payload: dict[str, object], timeout: int = 60) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _error_detail(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            return str(payload.get("detail") or payload)
        except Exception:  # noqa: BLE001 - reporting must not hide the original HTTP status.
            return f"http_{exc.code}"
    return f"{type(exc).__name__}:{exc}"


if __name__ == "__main__":
    raise SystemExit(main())
