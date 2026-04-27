from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api import auth_v17
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.infrastructure import auth_db
from v17_rebirth.backend.services import auth_service
from v17_rebirth.backend.services.wealth_timeline_preview import (
    WEALTH_TIMELINE_PREVIEW_PROTOCOL,
    attach_wealth_timeline_preview_meta,
    build_wealth_timeline_preview,
    summarize_wealth_timeline_preview,
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
        "birth_time_input": "1990-01-01T12:00:00",
        "birth_time": "1990-01-01T12:00:00",
        "birth_time_solar": "1990-01-01T12:00:00",
        "flow_year": 2026,
        "luck_pillar": "癸酉",
        "flow_pillar": "丙午",
        "four_pillars": {
            "year": "己巳",
            "month": "丙子",
            "day": "丙寅",
            "hour": "甲午",
        },
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


def test_wealth_timeline_preview_builds_current_luck_decade() -> None:
    preview = build_wealth_timeline_preview(physics_tensor=_tensor())

    assert preview["protocol"] == WEALTH_TIMELINE_PREVIEW_PROTOCOL
    assert preview["profile_present"] is True
    assert preview["timeline_ready"] is True
    assert preview["safety"]["raw_chart_access_for_llm"] is False
    assert preview["safety"]["parameter_mutation"] is False
    assert preview["luck_window"]["start_year"] <= 2026 <= preview["luck_window"]["end_year"]
    assert len(preview["decade_years"]) == 10
    assert preview["current_flow"]["year"] == 2026
    assert preview["current_flow"]["flow_pillar"]
    assert preview["top_attention_years"]

    serialized = json.dumps(preview, ensure_ascii=False)
    assert '"four_pillars"' not in serialized
    assert "birth_time_solar" not in serialized
    assert "flow_ten_gods" not in serialized


def test_wealth_timeline_preview_marks_years_with_attention_reasons() -> None:
    preview = build_wealth_timeline_preview(physics_tensor=_tensor())
    rows = preview["decade_years"]

    assert all(row["focus"] for row in rows)
    assert all(row["reasons"] for row in rows)
    assert all(row["suggested_actions"] for row in rows)
    assert all(row["money_signals"] for row in rows)
    assert {row["attention_level"] for row in rows} <= {"high", "medium", "steady"}
    assert {row["attention_type"] for row in rows} <= {
        "opportunity",
        "opportunity_with_risk",
        "risk_watch",
        "conversion_watch",
        "steady_watch",
    }


def test_wealth_timeline_preview_binds_mechanism_chains_to_years() -> None:
    preview = build_wealth_timeline_preview(physics_tensor=_tensor())
    year_rows = preview["top_attention_years"]

    assert year_rows
    binding_rows = [row for row in year_rows if row.get("activated_chains")]
    assert binding_rows
    sample = binding_rows[0]
    mechanism_snapshot = sample.get("mechanism_state_snapshot") or {}
    assert mechanism_snapshot.get("top_state")
    assert mechanism_snapshot.get("state_distribution")
    for key in {"closed", "partial_closed", "volatile", "open", "leaking", "blocked"}:
        assert isinstance(mechanism_snapshot.get(f"{key}_count"), (int, float))
        assert mechanism_snapshot.get(key + "_count", 0) >= 0
    for key in {"closed", "partial_closed", "volatile", "open", "leaking", "blocked"}:
        assert mechanism_snapshot["state_distribution"][key] >= 0
    assert sample["activated_chain_ids"]
    assert isinstance(sample["activated_chain_ids"], list)
    chain = sample["activated_chains"][0]
    assert chain["chain_id"]
    assert chain["closure_state"] in {"closed", "partial_closed", "open", "volatile", "blocked", "leaking"}
    assert chain["state_reason"]
    assert "path_score" in chain
    assert chain["path_score"] >= 0.0


def test_attach_wealth_timeline_preview_meta_keeps_prediction_audit() -> None:
    preview = build_wealth_timeline_preview(physics_tensor=_tensor())
    meta = attach_wealth_timeline_preview_meta({"existing": True}, preview)

    assert meta["existing"] is True
    assert meta["wealth_timeline_preview"]["protocol"] == WEALTH_TIMELINE_PREVIEW_PROTOCOL
    assert meta["topic_prediction_audits"][0]["kind"] == "timeline_preview"
    assert meta["topic_prediction_audits"][0]["top_attention_years"]


def test_wealth_timeline_summary_can_hide_decade_rows() -> None:
    preview = build_wealth_timeline_preview(physics_tensor=_tensor())
    summary = summarize_wealth_timeline_preview(preview, include_rows=False)

    assert summary["preview_present"] is True
    assert summary["timeline_ready"] is True
    assert "decade_years" not in summary
    assert summary["top_attention_years"]


def test_admin_wealth_timeline_preview_persists_to_session(isolated_auth_db) -> None:
    session_id = "wealth-timeline-api"
    asyncio.run(get_state_backend().set_physics(session_id, _tensor()))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.post(
            "/v17/admin/topic/wealth-timeline-preview",
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
    stored = asyncio.run(get_state_backend().get_physics(session_id))
    meta = stored["meta"]
    assert meta["wealth_timeline_preview"]["protocol"] == WEALTH_TIMELINE_PREVIEW_PROTOCOL
    assert meta["topic_prediction_audits"][0]["kind"] == "timeline_preview"


def test_admin_get_wealth_timeline_preview_returns_summary(isolated_auth_db) -> None:
    session_id = "wealth-timeline-get"
    tensor = _tensor()
    preview = build_wealth_timeline_preview(physics_tensor=tensor)
    tensor["meta"] = attach_wealth_timeline_preview_meta(tensor["meta"], preview)
    asyncio.run(get_state_backend().set_physics(session_id, tensor))

    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        response = client.get(
            (
                "/v17/admin/topic/wealth-timeline-preview"
                f"?v17_origin=v17_rebirth&session_id={session_id}&include_rows=false"
            ),
            cookies={"v17_session": admin_token},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["preview_present"] is True
    assert body["preview"]["protocol"] == WEALTH_TIMELINE_PREVIEW_PROTOCOL
    assert "decade_years" not in body["preview"]
    assert body["topic_prediction_audits"][0]["kind"] == "timeline_preview"
