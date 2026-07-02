from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _chart_payload() -> dict[str, object]:
    return load_synthetic_seeds(SEED_PATH)[0].chart_facts.model_dump(mode="json")


def _register(client: TestClient, email: str, role_key: str = "user") -> dict[str, object]:
    payload = {
        "email": email,
        "password": "abcd1235",
        "display_name": email.split("@", 1)[0],
        "role_key": role_key,
    }
    response = client.post(f"{API_PREFIX}/auth/register", json=payload)
    assert response.status_code == 200
    return response.json()


def _email(prefix: str) -> str:
    return f"{prefix}.{uuid4().hex}@example.com"


def test_phase54_user_registration_rejects_admin_and_creates_session() -> None:
    client = TestClient(create_app())

    admin_response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "email": "admin.phase54@example.com",
            "password": "abcd1235",
            "display_name": "admin",
            "role_key": "admin",
        },
    )
    assert admin_response.status_code == 422

    email = _email("user.phase54")
    registered = _register(client, email)
    assert registered["user"]["role_key"] == "user"
    assert registered["admin_registered"] is False
    me = client.get(f"{API_PREFIX}/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email


def test_phase54_profiles_are_scoped_to_logged_in_user_and_feed_dual_engine_report() -> None:
    client_a = TestClient(create_app())
    client_b = TestClient(create_app())
    _register(client_a, _email("a.phase54"))
    _register(client_b, _email("b.phase54"))
    chart = _chart_payload()
    ziwei = {
        "chart_id": "ziwei.phase54.profile.001",
        "life_palace": "命宫在寅",
        "body_palace": "身宫在申",
        "domain_lenses": {
            "career": "事业旁路关注平台、职责边界和外部机会。",
            "hidden_attribute": "保留反复出现的隐藏线索。",
        },
    }

    created = client_a.post(
        f"{API_PREFIX}/profiles",
        json={
            "display_name": "事业档案",
            "gender": chart["gender"],
            "chart_facts": chart,
            "ziwei_chart_facts": ziwei,
            "is_default": True,
        },
    )
    assert created.status_code == 200
    profile = created.json()["profile"]

    profiles_a = client_a.get(f"{API_PREFIX}/profiles").json()["profiles"]
    profiles_b = client_b.get(f"{API_PREFIX}/profiles").json()["profiles"]
    assert any(row["profile_id"] == profile["profile_id"] for row in profiles_a)
    assert not profiles_b

    report = client_a.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase54.profile.report",
            "reading_id": "reading.phase54.profile.report",
            "chart_facts": profile["chart_facts"],
            "ziwei_chart_facts": profile["ziwei_chart_facts"],
            "user_question": "这个八字今年事业适合稳定发展还是转型突破？",
            "topic": Topic.CAREER.value,
            "execution_mode": "local",
            "persist": False,
        },
    )
    assert report.status_code == 200
    body = report.json()
    engines = [result["engine"] for result in body["runtime"]["engine_result"]["results"]]
    assert "bazi" in engines
    assert "ziwei" in engines
    assert body["conversation_seeds"]


def test_phase54_user_ui_exposes_account_profile_probe_and_simple_dialogue_flow() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        "账号",
        "登录",
        "注册",
        "八字档案",
        "保存档案",
        "测算档案",
        "校准问题",
        "继续追问",
        "智能对话",
        "/api/v40/auth/",
        "/api/v40/profiles",
        "ziwei_chart_facts",
        "/api/v40/probes/answer",
        "/api/v40/conversation/turn",
    ]:
        assert text in html

    assert "我知道四柱" in html
    assert "我知道出生时间" in html
    assert "V30 多步" not in html
    assert "/admin/v40" not in html
    assert "role_key" not in html
    assert "role_context" not in html


def test_phase54_docs_schema_and_project_status_track_user_account_profile_flow() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE54_USER_ACCOUNT_PROFILE_FLOW.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    status = build_project_status()

    assert "User Account And Profile Flow" in doc
    assert "V30 multi-step reading pages are not kept" in doc
    assert "2026-07-02 Phase 54" in spec
    assert "docs/V40_PHASE54_USER_ACCOUNT_PROFILE_FLOW.md" in readme
    assert "v40_user_accounts" in schema
    assert "v40_user_sessions" in schema
    assert "v40_bazi_profiles" in schema
    assert status["current_phase"] == 54
    assert status["current_phase_name"] == "User Account And Profile Flow"
    assert any(row["range"] == "53" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "54" and row["status"] == "active" for row in status["phase_groups"])
    assert "UI-12: real-case account/profile acceptance" in status["next_mainline_tasks"]
