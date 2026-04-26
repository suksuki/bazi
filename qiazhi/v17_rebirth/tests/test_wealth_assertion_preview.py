from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api import auth_v17
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.infrastructure import auth_db
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
from v17_rebirth.backend.services import auth_service
from v17_rebirth.backend.services.wealth_assertion_preview import (
    WEALTH_ASSERTION_PREVIEW_PROTOCOL,
    attach_wealth_assertion_preview_meta,
    build_wealth_assertion_preview,
    summarize_wealth_assertion_preview,
)
from v17_rebirth.infrastructure.state_backend import get_state_backend


@pytest.fixture()
def isolated_auth_db(tmp_path: Path):
    storage = auth_db.V17AuthDB(tmp_path / "auth.db")
    auth_db.auth_storage = storage
    auth_service.auth_storage = storage
    auth_v17.auth_storage = storage
    return storage


def _tensor() -> dict:
    return {
        "gender": "male",
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_runtime": {
            "食神": 36.0,
            "伤官": 22.0,
            "正财": 30.0,
            "偏财": 20.0,
            "正官": 16.0,
            "七杀": 8.0,
            "正印": 10.0,
            "偏印": 6.0,
            "比肩": 10.0,
            "劫财": 8.0,
        },
        "facts": [
            {
                "fact": "格局候选：食伤生财，输出换财通道显性。",
                "plugin": "classical.pattern.shishen_shengcai.v1",
            },
            {"fact": "格局候选：正财格月令入口。", "plugin": "classical.pattern.wealth_star.v1"},
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "正财"],
                "taboo_gods": ["七杀"],
                "tongguan_gods": ["正官"],
                "confidence": 0.82,
            }
        },
    }


def test_wealth_assertion_preview_calls_llm_with_wealth_code_first(monkeypatch) -> None:
    captured: dict = {}

    def fake_chat(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "http_status": 200,
            "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
            "elapsed_ms": 12,
            "reply": "【财富总断】以输出变现为主，需以现金流承接。",
            "raw_response_json": {"choices": []},
        }

    monkeypatch.setattr(
        "v17_rebirth.backend.services.wealth_assertion_preview.get_runtime_llm_config",
        lambda: {
            "provider": "test",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "local-test",
            "http_timeout_sec": "3",
        },
    )

    preview = build_wealth_assertion_preview(
        physics_tensor=_tensor(),
        output_language="zh",
        execute_llm=True,
        llm_chat=fake_chat,
    )

    assert preview["protocol"] == WEALTH_ASSERTION_PREVIEW_PROTOCOL
    assert preview["code_source"] == "computed.from_server_physics"
    assert preview["code_present"] is True
    assert preview["profile_source"] == "computed.from_server_physics"
    assert preview["safety"]["llm_input_scope"] == "wealth_code_first_profile_fallback"
    assert preview["safety"]["raw_chart_access"] is False
    assert preview["llm_result"]["ok"] is True
    assert "wealth_code" in captured["messages"][1]["content"]
    assert "wealth_profile" in captured["messages"][1]["content"]
    assert "ten_gods_runtime" not in captured["messages"][1]["content"]
    assert "four_pillars" not in captured["messages"][1]["content"]
    assert captured["messages"][0]["role"] == "system"


def test_wealth_assertion_preview_refuses_without_profile_or_physics(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.services.wealth_assertion_preview.get_runtime_llm_config",
        lambda: {"provider": "test", "base_url": "http://127.0.0.1:11434/v1", "model": "local-test"},
    )

    preview = build_wealth_assertion_preview(execute_llm=True)

    assert preview["profile_present"] is False
    assert preview["material_present"] is False
    assert preview["llm_result"]["skipped"] is True
    assert preview["llm_result"]["reason"] == "missing_wealth_material"
    assert "缺少 wealth_code 和 wealth_profile" in preview["prompt_text"]


def test_wealth_assertion_preview_accepts_payload_wealth_code(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.services.wealth_assertion_preview.get_runtime_llm_config",
        lambda: {"provider": "test", "base_url": "", "model": ""},
    )
    code = resolve_wealth_code(_tensor())["wealth_code"]

    preview = build_wealth_assertion_preview(wealth_code=code, execute_llm=False)

    assert preview["code_present"] is True
    assert preview["profile_present"] is False
    assert preview["material_present"] is True
    assert preview["code_source"] == "payload.wealth_code"
    assert preview["prompt_contract"]["input_contract"] == "v17.topic.wealth_code.v1"


def test_attach_wealth_assertion_preview_meta_keeps_audit_trail() -> None:
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    preview = build_wealth_assertion_preview(wealth_profile=profile, execute_llm=False)

    meta = attach_wealth_assertion_preview_meta({"existing": True}, preview)

    assert meta["existing"] is True
    assert meta["wealth_assertion_preview"]["protocol"] == WEALTH_ASSERTION_PREVIEW_PROTOCOL
    assert meta["topic_assertion_audits"][0]["topic"] == "wealth"
    assert meta["topic_assertion_audits"][0]["code_present"] is False
    assert meta["topic_assertion_audits"][0]["profile_present"] is True


def test_wealth_assertion_preview_summary_hides_prompt_by_default() -> None:
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    preview = build_wealth_assertion_preview(wealth_profile=profile, execute_llm=False)

    summary = summarize_wealth_assertion_preview(preview, include_prompt=False, include_reply=False)

    assert summary["preview_present"] is True
    assert summary["wealth_code_summary"]["primary_wealth_path"] == {}
    assert summary["wealth_profile_summary"]["usable_state"] == profile["usable_state"]
    assert summary["wealth_profile_summary"]["top_channel"]["id"] == profile["primary_channels"][0]["id"]
    assert "prompt_text" not in summary
    assert "prompt_contract" not in summary
    assert "raw_response_json" not in summary["llm_result_summary"]
    assert "reply_preview" in summary["llm_result_summary"]


def test_admin_wealth_assertion_preview_persists_backstage_audit(isolated_auth_db) -> None:
    session_id = "wealth-preview-api"
    asyncio.run(get_state_backend().set_physics(session_id, _tensor()))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.post(
            "/v17/admin/topic/wealth-assertion-preview",
            cookies={"v17_session": admin_token},
            json={
                "v17_origin": "v17_rebirth",
                "session_id": session_id,
                "execute_llm": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["persisted"] is True
    assert body["preview"]["llm_result"]["reason"] == "execute_llm_disabled"
    stored = asyncio.run(get_state_backend().get_physics(session_id))
    meta = stored["meta"]
    assert meta["wealth_assertion_preview"]["protocol"] == WEALTH_ASSERTION_PREVIEW_PROTOCOL
    assert meta["wealth_assertion_preview"]["safety"]["raw_chart_access"] is False
    assert meta["wealth_assertion_preview"]["code_present"] is True


def test_admin_get_wealth_assertion_preview_returns_audit_summary(isolated_auth_db) -> None:
    session_id = "wealth-preview-audit-get"
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    preview = build_wealth_assertion_preview(wealth_profile=profile, execute_llm=False)
    tensor = _tensor()
    tensor["meta"] = attach_wealth_assertion_preview_meta(tensor["meta"], preview)
    asyncio.run(get_state_backend().set_physics(session_id, tensor))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.get(
            (
                "/v17/admin/topic/wealth-assertion-preview"
                f"?v17_origin=v17_rebirth&session_id={session_id}&include_reply=false"
            ),
            cookies={"v17_session": admin_token},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["preview_present"] is True
    assert body["preview"]["protocol"] == WEALTH_ASSERTION_PREVIEW_PROTOCOL
    assert body["preview"]["wealth_profile_summary"]["top_channel"]["id"] == profile["primary_channels"][0]["id"]
    assert "prompt_text" not in body["preview"]
    assert "reply_preview" in body["preview"]["llm_result_summary"]
    assert body["topic_assertion_audits"][0]["topic"] == "wealth"


def test_admin_get_wealth_assertion_preview_can_include_prompt(isolated_auth_db) -> None:
    session_id = "wealth-preview-audit-prompt-get"
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    preview = build_wealth_assertion_preview(wealth_profile=profile, execute_llm=False)
    tensor = _tensor()
    tensor["meta"] = attach_wealth_assertion_preview_meta(tensor["meta"], preview)
    asyncio.run(get_state_backend().set_physics(session_id, tensor))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.get(
            (
                "/v17/admin/topic/wealth-assertion-preview"
                f"?v17_origin=v17_rebirth&session_id={session_id}&include_prompt=true"
            ),
            cookies={"v17_session": admin_token},
        )

    assert response.status_code == 200
    preview_body = response.json()["preview"]
    assert "prompt_text" in preview_body
    assert "没有 wealth_code 时，才退回使用 wealth_profile" in preview_body["prompt_text"]
    assert preview_body["prompt_contract"]["task_type"] == "wealth_topic_assertion"
