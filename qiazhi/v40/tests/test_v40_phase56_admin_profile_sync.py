from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import v40.api.app as api_app
from v40.api.app import API_PREFIX, create_app
from v40.auth.accounts import (
    BUILTIN_ADMIN_EMAIL,
    BUILTIN_ADMIN_PASSWORD,
    BUILTIN_ADMIN_USERNAME,
    build_builtin_admin_account,
    verify_password,
)
from v40.migration.admin_v30_profiles import convert_v30_profile_to_v40, load_v30_product_store, select_v30_admin_profiles
from v40.project import build_project_status


ROOT = Path(__file__).resolve().parents[1]
V30_STORE = ROOT.parent / "v30" / ".runtime" / "remote_product_sync" / "product_ui_store.13.json"


def _reset_memory(monkeypatch) -> None:
    monkeypatch.setattr(api_app, "_repository_or_none", lambda: None)
    api_app._MEMORY_ACCOUNTS_BY_EMAIL.clear()
    api_app._MEMORY_ACCOUNTS_BY_ID.clear()
    api_app._MEMORY_SESSIONS.clear()
    api_app._MEMORY_PROFILES_BY_USER.clear()


def test_phase56_builtin_admin_is_practitioner_with_fixed_email_and_password() -> None:
    admin = build_builtin_admin_account()

    assert admin.user_id == "user:admin"
    assert admin.email == BUILTIN_ADMIN_EMAIL
    assert admin.display_name == BUILTIN_ADMIN_USERNAME
    assert admin.role_key == "practitioner"
    assert verify_password(BUILTIN_ADMIN_PASSWORD, password_hash=admin.password_hash, password_salt=admin.password_salt)


def test_phase56_admin_can_login_by_username_and_registration_cannot_claim_admin(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    admin = build_builtin_admin_account()
    api_app._save_account(admin)
    client = TestClient(create_app())

    login = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": BUILTIN_ADMIN_USERNAME, "password": BUILTIN_ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["user"]["email"] == BUILTIN_ADMIN_EMAIL
    assert body["user"]["role_key"] == "practitioner"

    me = client.get(f"{API_PREFIX}/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["display_name"] == "admin"

    claimed = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "email": BUILTIN_ADMIN_EMAIL,
            "password": BUILTIN_ADMIN_PASSWORD,
            "display_name": "admin",
            "role_key": "practitioner",
        },
    )
    assert claimed.status_code == 403


def test_phase56_selects_v30_admin_profiles_and_converts_profile_contract() -> None:
    store = load_v30_product_store(V30_STORE)
    admin_profiles = select_v30_admin_profiles(store)

    assert len(admin_profiles) == 18
    assert {row["display_name"] for row in admin_profiles} >= {"刘晋", "秦姥姥", "朱甫晓"}

    def fake_chart_builder(_profile, _target_year):
        return {
            "status": "ready",
            "pillars": {"year": "甲子", "month": "戊辰", "day": "丙午", "hour": "辛卯"},
            "current_luck": "甲辰",
            "current_year": "丙午",
        }

    converted = convert_v30_profile_to_v40(admin_profiles[0], chart_builder=fake_chart_builder, is_default=True)
    assert converted.user_id == "user:admin"
    assert converted.profile_id.startswith("v30-admin:")
    assert converted.is_default is True
    assert converted.chart_facts.pillars_text == "甲子 戊辰 丙午 辛卯"
    assert converted.chart_facts.current_luck == "甲辰"
    assert converted.chart_facts.current_year == "丙午"
    assert "v30_admin_import" in converted.tags


def test_phase56_docs_and_status_track_admin_profile_sync() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE56_ADMIN_PROFILE_SYNC.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "admin / abcd1235" in doc
    assert "jerrydidi@gmail.com" in doc
    assert "18 个 V30 admin 八字档案" in doc
    assert "2026-07-02 Phase 56" in spec
    assert "docs/V40_PHASE56_ADMIN_PROFILE_SYNC.md" in readme
    assert status["current_phase"] == 59
    assert status["current_phase_name"] == "UI Product Convergence Runtime"
    assert any(row["range"] == "56" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "active" for row in status["phase_groups"])
