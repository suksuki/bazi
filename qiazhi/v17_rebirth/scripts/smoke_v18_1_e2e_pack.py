#!/usr/bin/env python3
"""P3-C E2E smoke pack for the v18.1 predictive product loop.

This script verifies the audited main product path:

    admin bootstrap
    -> active rule
    -> user agent prediction
    -> verified explanation
    -> feedback learning_signal
    -> replay

Run from the repo root:

    python v17_rebirth/scripts/smoke_v18_1_e2e_pack.py \
      --base-url http://127.0.0.1:8017 \
      --frontend-url http://127.0.0.1:3001 \
      --skip-bootstrap-if-active \
      --verbose

If the active rule store is empty, bootstrap requires an admin login cookie:

    python v17_rebirth/scripts/smoke_v18_1_e2e_pack.py \
      --admin-cookie 'v17_session=...' \
      --base-url http://127.0.0.1:8017

Guardrails:
- Does not hardcode real passwords.
- Does not write directly to a database.
- Does not inject sandbox/seed rules into user prediction.
- Uses the official admin bootstrap lifecycle when a bootstrap is needed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class HttpResult:
    status: int
    body: str
    json_body: Any


class SmokeFailure(Exception):
    def __init__(self, step: str, message: str, *, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.step = step
        self.status = status
        self.body = body


def _json_dumps(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _unwrap(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("data"), dict):
        return value["data"]
    return value if isinstance(value, dict) else {}


def _items(value: Any) -> list[Any]:
    if isinstance(value, dict):
        raw = value.get("items") or value.get("active_rules") or value.get("rules") or []
        return raw if isinstance(raw, list) else []
    return []


def _safe_str(value: Any, default: str = "") -> str:
    text = "" if value is None else str(value).strip()
    return text or default


def _short(value: str, width: int = 18) -> str:
    return value if len(value) <= width else f"{value[: width - 3]}..."


def _recursive_has_key_or_text(value: Any, needle: str) -> bool:
    needle = needle.lower()
    if isinstance(value, dict):
        for key, item in value.items():
            if needle in str(key).lower():
                return True
            if _recursive_has_key_or_text(item, needle):
                return True
    elif isinstance(value, list):
        return any(_recursive_has_key_or_text(item, needle) for item in value)
    elif isinstance(value, str):
        return needle in value.lower()
    return False


class SmokeClient:
    def __init__(self, *, base_url: str, frontend_url: str, admin_cookie: str, verbose: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.frontend_url = frontend_url.rstrip("/")
        self.admin_cookie = admin_cookie.strip()
        self.verbose = verbose

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        payload: dict[str, Any] | None = None,
        cookie: str = "",
        step: str,
        absolute: bool = False,
        expected: tuple[int, ...] = (200,),
    ) -> HttpResult:
        url = path_or_url if absolute else f"{self.base_url}{path_or_url}"
        body = _json_dumps(payload) if payload is not None else None
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        if self.verbose:
            print(f"  -> {method.upper()} {url}")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                result = HttpResult(status=int(resp.status), body=text, json_body=_parse_json(text))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            result = HttpResult(status=int(exc.code), body=text, json_body=_parse_json(text))
        except urllib.error.URLError as exc:
            raise SmokeFailure(step, f"request failed: {exc}") from exc

        if self.verbose:
            preview = result.body if len(result.body) <= 1200 else f"{result.body[:1200]}..."
            print(f"  <- HTTP {result.status} {preview}")

        if result.status not in expected:
            raise SmokeFailure(step, f"unexpected HTTP status {result.status}", status=result.status, body=result.body)
        return result


def _assert_ok(result: HttpResult, step: str) -> dict[str, Any]:
    if not isinstance(result.json_body, dict):
        raise SmokeFailure(step, "response is not JSON", status=result.status, body=result.body)
    if result.json_body.get("ok") is False:
        code = _safe_str(result.json_body.get("code"), "UNKNOWN")
        message = _safe_str(result.json_body.get("message"), "request failed")
        raise SmokeFailure(step, f"{code}: {message}", status=result.status, body=result.body)
    return _unwrap(result.json_body)


def _active_rules(client: SmokeClient, step: str) -> list[dict[str, Any]]:
    result = client.request("GET", "/v18.1/rule-kernels?status=active", step=step)
    data = _assert_ok(result, step)
    return [item for item in _items(data) if isinstance(item, dict)]


def _frontend_preflight(client: SmokeClient) -> None:
    step = "[1/7] active rule precheck"
    if not client.frontend_url:
        return
    result = client.request(
        "GET",
        f"{client.frontend_url}/",
        step=step,
        absolute=True,
        expected=(200, 302, 307, 308),
    )
    print(f"  frontend preflight: HTTP {result.status}")


def step_1_precheck(client: SmokeClient) -> list[dict[str, Any]]:
    print("[1/7] active rule precheck")
    _frontend_preflight(client)
    rules = _active_rules(client, "[1/7] active rule precheck")
    print(f"  active_rule_count={len(rules)}")
    return rules


def step_2_bootstrap(client: SmokeClient, *, skip: bool, active_rules: list[dict[str, Any]]) -> None:
    print("[2/7] admin bootstrap")
    if active_rules and skip:
        print("  skipped because active rule already exists and --skip-bootstrap-if-active is set")
        return
    result = client.request(
        "POST",
        "/v18.1/admin/rule-bootstrap/wealth",
        payload={
            "bootstrap_id": f"p3c_{int(time.time())}",
            "rule_id": "bootstrap.wealth.baseline",
        },
        cookie=client.admin_cookie,
        step="[2/7] admin bootstrap",
        expected=(200, 403),
    )
    if result.status == 403:
        body = result.body
        if "ADMIN_REQUIRED" in body:
            raise SmokeFailure(
                "[2/7] admin bootstrap",
                "ADMIN_REQUIRED: bootstrap needs an admin session. Log in as admin or pass --admin-cookie 'v17_session=...'.",
                status=result.status,
                body=body,
            )
        raise SmokeFailure("[2/7] admin bootstrap", "bootstrap forbidden", status=result.status, body=body)
    data = _assert_ok(result, "[2/7] admin bootstrap")
    steps = data.get("steps") if isinstance(data.get("steps"), list) else []
    for row in steps:
        if isinstance(row, dict):
            print(
                "  step={step} status={status} object_id={object_id} audit_event_id={audit}".format(
                    step=_safe_str(row.get("step_key")),
                    status=_safe_str(row.get("status")),
                    object_id=_safe_str(row.get("object_id"), "n/a"),
                    audit=_short(_safe_str(row.get("audit_event_id"), "n/a")),
                )
            )


def step_3_postcheck(client: SmokeClient) -> list[dict[str, Any]]:
    print("[3/7] active rule postcheck")
    rules = _active_rules(client, "[3/7] active rule postcheck")
    if not rules:
        raise SmokeFailure("[3/7] active rule postcheck", "active rule count is 0 after bootstrap")
    for rule in rules[:5]:
        print(
            "  active rule_id={rule_id} version={version} content_hash={content_hash}".format(
                rule_id=_safe_str(rule.get("rule_id")),
                version=_safe_str(rule.get("version")),
                content_hash=_short(_safe_str(rule.get("content_hash"))),
            )
        )
    return rules


def step_4_agent_prediction(client: SmokeClient) -> tuple[str, str, str]:
    print("[4/7] agent prediction")
    session_result = client.request(
        "POST",
        "/v18.1/agent/sessions",
        payload={"surface": "p3c_e2e_smoke", "user_locale": "zh-CN"},
        step="[4/7] agent prediction",
    )
    session = _assert_ok(session_result, "[4/7] agent prediction")
    session_id = _safe_str(session.get("agent_session_id") or session.get("session_id") or session.get("id"))
    if not session_id:
        raise SmokeFailure("[4/7] agent prediction", "agent session response missing session id", body=session_result.body)
    print(f"  session_id={session_id}")

    turn_result = client.request(
        "POST",
        f"/v18.1/agent/sessions/{urllib.parse.quote(session_id)}/turns",
        payload={
            "request_id": f"p3c_turn_{int(time.time())}",
            "user_message": "我未来两年财运怎么样？",
            "user_query": "我未来两年财运怎么样？",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "p3c_e2e_smoke"}],
            "birth_payload": {"year": "1990", "month": "01", "day": "01", "hour": "09", "gender": "male"},
            "chart_snapshot": {
                "source": "p3c_e2e_smoke",
                "completeness": "complete_birth_fields",
                "birth_time": "1990-01-01T09:00:00",
                "calendar": "solar",
                "gender": "male",
                "matched_facts": ["complete_birth_fields"],
                "birth_fields": {"year": "1990", "month": "01", "day": "01", "hour": "09", "gender": "male"},
                "four_pillars": {"year": "1990", "month": "01", "day": "01", "hour": "09"},
            },
            "missing_info_policy": "clarify_before_predict",
        },
        step="[4/7] agent prediction",
    )
    turn_data = _assert_ok(turn_result, "[4/7] agent prediction")
    safe_output = turn_data.get("safe_output") if isinstance(turn_data.get("safe_output"), dict) else {}
    if _safe_str(safe_output.get("type")) == "clarification_question" or safe_output.get("is_prediction") is False:
        raise SmokeFailure("[4/7] agent prediction", "agent returned clarification instead of prediction", status=turn_result.status, body=turn_result.body)
    prediction_id = _safe_str(turn_data.get("prediction_id"))
    contract_id = _safe_str(turn_data.get("contract_id"))
    if not prediction_id:
        raise SmokeFailure("[4/7] agent prediction", "prediction_id missing", status=turn_result.status, body=turn_result.body)
    if "RULE_SCOPE_VIOLATION" in turn_result.body:
        raise SmokeFailure("[4/7] agent prediction", "RULE_SCOPE_VIOLATION", status=turn_result.status, body=turn_result.body)
    conclusion_ref = _extract_conclusion_ref(safe_output)
    print(f"  prediction_id={prediction_id}")
    print(f"  contract_id={contract_id or 'n/a'}")
    print(f"  conclusion_ref={conclusion_ref or 'n/a'}")
    return prediction_id, contract_id, conclusion_ref


def _extract_conclusion_ref(safe_output: Any) -> str:
    if not isinstance(safe_output, dict):
        return ""
    for key in ("conclusion_ref", "conclusion_id"):
        value = _safe_str(safe_output.get(key))
        if value:
            return value
    for key in ("conclusion_refs", "conclusion_ids"):
        values = safe_output.get(key)
        if isinstance(values, list) and values:
            value = _safe_str(values[0])
            if value:
                return value
    sections = safe_output.get("sections")
    if isinstance(sections, dict):
        for key in ("conclusion_refs", "conclusion_ids"):
            values = sections.get(key)
            if isinstance(values, list) and values:
                value = _safe_str(values[0])
                if value:
                    return value
    return "conclusion_1"


def step_5_explanation(client: SmokeClient, prediction_id: str, contract_id: str) -> None:
    print("[5/7] explanation")
    result = client.request(
        "POST",
        f"/v18.1/predictions/{urllib.parse.quote(prediction_id)}/explain",
        payload={
            "prediction_id": prediction_id,
            "contract_id": contract_id,
            "allowed_output_scope": "verified_prediction_explanation",
            "user_locale": "zh-CN",
            "tone": "calm",
            "explanation_level": "normal",
            "include_uncertainty": True,
            "include_evidence_trace": True,
        },
        step="[5/7] explanation",
    )
    data = _assert_ok(result, "[5/7] explanation")
    response = data.get("explanation_response") if isinstance(data.get("explanation_response"), dict) else data
    verifier = response.get("verifier") if isinstance(response.get("verifier"), dict) else {}
    verified = response.get("verified") is True or verifier.get("ok") is True or _safe_str(verifier.get("action")).lower() in {"allow", "allowed", "verified"}
    if not verified:
        raise SmokeFailure("[5/7] explanation", "explanation is not verified/safe", status=result.status, body=result.body)
    if any(key in result.body for key in ("raw_llm_output", "llm_raw", "raw_output")):
        raise SmokeFailure("[5/7] explanation", "raw LLM output leaked in explanation response", status=result.status, body=result.body)
    if not (_recursive_has_key_or_text(data, "uncertainty") or "不确定" in result.body):
        raise SmokeFailure("[5/7] explanation", "explanation response missing uncertainty", status=result.status, body=result.body)
    print("  verified explanation generated")


def step_6_feedback(client: SmokeClient, prediction_id: str, conclusion_ref: str) -> tuple[str, str]:
    print("[6/7] feedback")
    result = client.request(
        "POST",
        f"/v18.1/predictions/{urllib.parse.quote(prediction_id)}/feedback",
        payload={
            "request_id": f"p3c_feedback_{int(time.time())}",
            "prediction_id": prediction_id,
            "conclusion_ref": conclusion_ref or "conclusion_1",
            "conclusion_id": conclusion_ref or "conclusion_1",
            "feedback_type": "partial",
            "user_comment": "P3-C smoke feedback: partially matches observed reality.",
            "observed_event": {"source": "p3c_e2e_smoke", "label": "partial"},
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        step="[6/7] feedback",
    )
    data = _assert_ok(result, "[6/7] feedback")
    feedback = data.get("feedback") if isinstance(data.get("feedback"), dict) else {}
    signal = data.get("learning_signal") if isinstance(data.get("learning_signal"), dict) else {}
    feedback_id = _safe_str(feedback.get("feedback_id") or feedback.get("id"))
    signal_id = _safe_str(signal.get("signal_id") or signal.get("id"))
    if not feedback_id:
        raise SmokeFailure("[6/7] feedback", "feedback_id missing", status=result.status, body=result.body)
    if not signal_id:
        raise SmokeFailure("[6/7] feedback", "learning_signal/signal_id missing", status=result.status, body=result.body)
    print(f"  feedback_id={feedback_id}")
    print(f"  signal_id={signal_id}")
    return feedback_id, signal_id


def step_7_replay(client: SmokeClient, prediction_id: str) -> None:
    print("[7/7] replay")
    result = client.request(
        "GET",
        f"/v18.1/predictions/{urllib.parse.quote(prediction_id)}/replay",
        step="[7/7] replay",
    )
    data = _assert_ok(result, "[7/7] replay")
    ledger = data.get("ledger")
    contract = data.get("contract")
    evidence = data.get("evidence")
    feedback = data.get("feedback")
    signals = data.get("learning_signals") or data.get("learning_signal")
    missing = [
        name
        for name, value in {
            "ledger": ledger,
            "contract": contract,
            "evidence": evidence,
            "feedback": feedback,
            "learning_signal": signals,
        }.items()
        if value in (None, [], {})
    ]
    if missing:
        raise SmokeFailure("[7/7] replay", f"replay missing required fields: {', '.join(missing)}", status=result.status, body=result.body)
    if "rule_drift" in data:
        print(f"  rule_drift={data.get('rule_drift')}")
    print("  replay contains ledger + contract + evidence + feedback + learning_signal")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P3-C v18.1 E2E smoke pack")
    parser.add_argument("--base-url", default="http://127.0.0.1:8017")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:3001")
    parser.add_argument("--admin-cookie", default="")
    parser.add_argument("--skip-bootstrap-if-active", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    client = SmokeClient(
        base_url=args.base_url,
        frontend_url=args.frontend_url,
        admin_cookie=args.admin_cookie,
        verbose=args.verbose,
    )
    try:
        active_rules = step_1_precheck(client)
        step_2_bootstrap(client, skip=args.skip_bootstrap_if_active, active_rules=active_rules)
        step_3_postcheck(client)
        prediction_id, contract_id, conclusion_ref = step_4_agent_prediction(client)
        step_5_explanation(client, prediction_id, contract_id)
        step_6_feedback(client, prediction_id, conclusion_ref)
        step_7_replay(client, prediction_id)
    except SmokeFailure as exc:
        print(f"\nP3-C E2E smoke pack failed at {exc.step}", file=sys.stderr)
        print(f"Reason: {exc}", file=sys.stderr)
        if exc.status is not None:
            print(f"HTTP status: {exc.status}", file=sys.stderr)
        if exc.body:
            print("Response body:", file=sys.stderr)
            print(exc.body, file=sys.stderr)
        return 1
    print("P3-C E2E smoke pack passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

