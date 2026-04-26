from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api import auth_v17
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.infrastructure import auth_db
from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import resolve_bazi_image
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile
from v17_rebirth.backend.services import auth_service
from v17_rebirth.backend.services.wealth_code_preview import (
    WEALTH_CODE_PREVIEW_PROTOCOL,
    attach_wealth_code_preview_meta,
    build_wealth_code_preview,
    summarize_wealth_code_preview,
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
        "day_master_stem": "庚",
        "four_pillars": {
            "year": "甲子",
            "month": "丙寅",
            "day": "庚申",
            "hour": "壬午",
        },
        "luck_pillar": "壬午",
        "flow_pillar": "甲辰",
        "ten_gods_runtime": {
            "食神": 40.0,
            "伤官": 10.0,
            "七杀": 58.0,
            "正官": 8.0,
            "偏财": 24.0,
            "正财": 6.0,
            "正印": 8.0,
            "偏印": 4.0,
            "比肩": 8.0,
            "劫财": 5.0,
        },
        "facts": [
            {
                "fact": "格局候选：食神制杀，靠输出能力处理压力与复杂任务。",
                "plugin": "classical.pattern.shishen_zhisha.v1",
            },
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "偏财"],
                "taboo_gods": ["七杀"],
                "confidence": 0.8,
            }
        },
    }


def _hydrated_tensor() -> dict:
    tensor = _tensor()
    tensor["meta"]["bazi_image"] = resolve_bazi_image(tensor)["bazi_image"]
    tensor["meta"]["wealth_profile"] = resolve_wealth_profile(tensor)["wealth_profile"]
    tensor["meta"]["wealth_code"] = resolve_wealth_code(tensor)["wealth_code"]
    return tensor


def test_wealth_code_preview_builds_backstage_payload() -> None:
    preview = build_wealth_code_preview(physics_tensor=_tensor())

    assert preview["protocol"] == WEALTH_CODE_PREVIEW_PROTOCOL
    assert preview["code_present"] is True
    assert preview["code_source"] == "computed.from_server_physics"
    assert preview["safety"]["raw_chart_access_for_llm"] is False
    assert preview["safety"]["parameter_mutation"] is False
    assert preview["wealth_code"]["primary_wealth_path"]["id"] == "output_controls_pressure"
    assert preview["path_summary"]["primary_path_label"] == "靠解决难题赚钱"


def test_attach_wealth_code_preview_meta_keeps_code_audit() -> None:
    preview = build_wealth_code_preview(physics_tensor=_tensor())
    meta = attach_wealth_code_preview_meta({"existing": True}, preview)

    assert meta["existing"] is True
    assert meta["wealth_code_preview"]["protocol"] == WEALTH_CODE_PREVIEW_PROTOCOL
    assert meta["wealth_code"]["contract"] == "v17.topic.wealth_code.v1"
    assert meta["topic_code_audits"][0]["kind"] == "wealth_code_preview"
    assert meta["topic_code_audits"][0]["primary_path_id"] == "output_controls_pressure"


def test_wealth_code_preview_summary_can_hide_full_code_and_graph() -> None:
    preview = build_wealth_code_preview(physics_tensor=_tensor())
    summary = summarize_wealth_code_preview(preview, include_code=False, include_graph=False)

    assert summary["preview_present"] is True
    assert summary["path_summary"]["primary_path_id"] == "output_controls_pressure"
    assert "wealth_code" not in summary
    assert "evidence_graph" not in summary["wealth_code_summary"]


def test_admin_wealth_code_preview_persists_to_session(isolated_auth_db) -> None:
    session_id = "wealth-code-preview-api"
    asyncio.run(get_state_backend().set_physics(session_id, _tensor()))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.post(
            "/v17/admin/topic/wealth-code-preview",
            cookies={"v17_session": admin_token},
            json={
                "v17_origin": "v17_rebirth",
                "session_id": session_id,
                "persist": True,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["persisted"] is True
    assert body["preview"]["path_summary"]["primary_path_id"] == "output_controls_pressure"
    stored = asyncio.run(get_state_backend().get_physics(session_id))
    meta = stored["meta"]
    assert meta["wealth_code_preview"]["protocol"] == WEALTH_CODE_PREVIEW_PROTOCOL
    assert meta["wealth_code"]["contract"] == "v17.topic.wealth_code.v1"
    assert meta["topic_code_audits"][0]["kind"] == "wealth_code_preview"


def test_admin_get_wealth_code_preview_returns_summary(isolated_auth_db) -> None:
    session_id = "wealth-code-preview-get"
    tensor = _hydrated_tensor()
    preview = build_wealth_code_preview(wealth_code=tensor["meta"]["wealth_code"])
    tensor["meta"] = attach_wealth_code_preview_meta(tensor["meta"], preview)
    asyncio.run(get_state_backend().set_physics(session_id, tensor))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.get(
            (
                "/v17/admin/topic/wealth-code-preview"
                f"?v17_origin=v17_rebirth&session_id={session_id}&include_code=false&include_graph=false"
            ),
            cookies={"v17_session": admin_token},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["preview_present"] is True
    assert body["preview"]["protocol"] == WEALTH_CODE_PREVIEW_PROTOCOL
    assert body["preview"]["path_summary"]["primary_path_id"] == "output_controls_pressure"
    assert "wealth_code" not in body["preview"]
    assert "evidence_graph" not in body["preview"]["wealth_code_summary"]
    assert body["topic_code_audits"][0]["kind"] == "wealth_code_preview"
