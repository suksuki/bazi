from __future__ import annotations

import json
from pathlib import Path


def _agent_turn_payload(locale: str, question_key: str, message: str) -> dict:
    return {
        "birth_input": {
            "year": 1990,
            "month": 4,
            "day": 15,
            "hour": 9,
            "minute": 0,
            "gender": "unknown",
            "calendar_type": "solar",
        },
        "selected_year": 2026,
        "selected_question_key": question_key,
        "message": message,
        "locale": locale,
        "session_id": "p67_multilingual_test",
    }


def test_p67_agent_turn_localizes_guided_answer_surface(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import v19.runtime as runtime
    import v19.server as server

    settings = runtime.default_settings()
    settings["llm"]["enabled"] = False
    settings["llm"]["execute_llm"] = False
    monkeypatch.setattr(server, "load_settings", lambda: settings)
    monkeypatch.setattr(server, "get_session", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        server,
        "create_or_append_session",
        lambda payload, turn, settings=None: {
            "session_id": payload.get("session_id") or "p67_multilingual_test",
            "role": payload.get("role") or "admin",
            "turns": [turn],
            "storage": {"backend": "test_no_write"},
        },
    )

    client = TestClient(server.app)
    cases = [
        (
            "en",
            "q_relationship_structure",
            "How should relationship structure be read?",
            "Relationship",
            "relationship",
        ),
        (
            "ko",
            "q_health_structure",
            "건강 구조는 어떻게 읽어야 하나요?",
            "건강",
            "구조",
        ),
    ]
    for locale, key, message, required_a, required_b in cases:
        response = client.post("/api/agent/turn?role=admin", json=_agent_turn_payload(locale, key, message))
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        data = payload["data"]
        reply_text = "\n".join(data["agent_reply"]["content"])
        answer = data["guided_question_answer"]

        assert data["locale"] == locale
        assert data["agent_reply"]["locale"] == locale
        assert answer["selected_locale"] == locale
        assert required_a in reply_text
        assert required_b in reply_text
        assert "你问的是" not in reply_text
        assert {"zh", "en", "ko"} <= set(answer["text"])
        assert {"zh", "en", "ko"} <= set(answer["content"])
        assert answer["text"][locale].strip() == reply_text.strip()


def test_p67_frontend_sends_locale_with_agent_turn_payload() -> None:
    root = Path(__file__).resolve().parents[2]
    oracle_js = (root / "v19/frontend/assets/oracle.js").read_text(encoding="utf-8")
    app_js = (root / "v19/frontend/assets/app.js").read_text(encoding="utf-8")

    assert 'postJson("/api/agent/turn"' in oracle_js
    assert "session_id: sessionId, locale" in oracle_js
    assert 'locale: localStorage.getItem("v19_oracle_locale") || "zh"' in app_js


def test_p67_income_renderer_supports_answer_locales() -> None:
    from v19.agent.income_stability import derive_income_stability
    from v19.agent.renderers import render_income_stability_answer
    from v19.agent.structure import build_agent_turn

    result = build_agent_turn(
        {
            "birth_input": {
                "year": 1990,
                "month": 4,
                "day": 15,
                "hour": 9,
                "minute": 0,
                "gender": "unknown",
                "calendar_type": "solar",
            },
            "selected_year": 2026,
            "message": "income structure",
        }
    )
    bundle = derive_income_stability(result["data"]["chart"])
    zh = render_income_stability_answer(bundle, locale="zh")
    en = render_income_stability_answer(bundle, locale="en")
    ko = render_income_stability_answer(bundle, locale="ko")

    assert "这张命盘的收入稳定性结构先看作" in zh
    assert "income-stability structure" in en
    assert "这张命盘" not in en
    assert "소득 안정성 구조" in ko
    assert "这张命盘" not in ko


def test_p68_test_tier_scripts_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    scripts = {
        "fast": root / "v19/scripts/test_fast.sh",
        "targeted": root / "v19/scripts/test_targeted.sh",
        "full": root / "v19/scripts/test_full.sh",
    }

    for script in scripts.values():
        text = script.read_text(encoding="utf-8")
        assert "pytest" in text
        assert "cd \"$(dirname \"$0\")/../..\"" in text

    assert "-m py_compile" in scripts["fast"].read_text(encoding="utf-8")
    assert "test_p67_p68_multilingual_and_test_tiers.py" in scripts["targeted"].read_text(encoding="utf-8")
    assert 'v19/tests "$@"' in scripts["full"].read_text(encoding="utf-8")
    assert "docs/v19/V19_P67_MULTILINGUAL_ANSWER_SURFACE.md" in manifest["created_from"]
    assert "docs/v19/V19_P68_TEST_TIERS.md" in manifest["created_from"]
    assert manifest["p67_multilingual_answer_surface"]["supported_locales"] == ["zh", "en", "ko"]
    assert manifest["p68_test_tiers"]["tiers"] == ["fast", "targeted", "full"]
    assert "P67_MULTILINGUAL_ANSWER_SURFACE" in manifest["guardrails"]
    assert "P68_TEST_TIERS" in manifest["guardrails"]
