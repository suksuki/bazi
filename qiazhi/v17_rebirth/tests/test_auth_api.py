from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.api import auth_v17
from v17_rebirth.backend.infrastructure import auth_db
from v17_rebirth.backend.services import auth_service


@pytest.fixture()
def isolated_auth_db(tmp_path: Path):
    storage = auth_db.V17AuthDB(tmp_path / "auth.db")
    auth_db.auth_storage = storage
    auth_service.auth_storage = storage
    auth_v17.auth_storage = storage
    return storage


def test_register_bootstraps_first_admin_and_me(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={
                "identifier": "admin",
                "password": "abcd1235",
            },
        )
        assert admin_login.status_code == 200
        assert admin_login.json()["user"]["role"] == "admin"

        r = client.post(
            "/v17/auth/register",
            json={
                "username": "founder",
                "display_name": "Founder",
                "email": "founder@example.com",
                "password": "very-secure-pass",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["bootstrap_admin"] is False
        assert body["user"]["role"] == "user"

        token = body["session_token"]
        me = client.get("/v17/auth/me", cookies={"v17_session": token})
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["user"]["username"] == "founder"
        assert "oracle.access" in me_body["user"]["capabilities"]
        assert me_body["user"]["surface_access"]["oracle"] == ["core", "auxiliary"]
        assert me_body["user"]["surface_access"]["admin"] is False


def test_second_user_defaults_to_user_and_manager_can_promote_non_admin(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]

        second = client.post(
            "/v17/auth/register",
            json={"username": "operator", "password": "very-secure-pass", "display_name": "Operator"},
            headers={"x-forwarded-for": "203.0.113.25"},
        )
        second_body = second.json()
        assert second_body["user"]["role"] == "user"
        operator_id = int(second_body["user"]["id"])

        list_resp = client.get("/v17/auth/users", cookies={"v17_session": admin_token})
        assert list_resp.status_code == 200
        assert len(list_resp.json()["users"]) == 2
        operator_row = next(row for row in list_resp.json()["users"] if row["username"] == "operator")
        assert operator_row["latest_ip_address"] == "203.0.113.25"

        promote = client.post(
            f"/v17/auth/users/{operator_id}/role",
            json={"role": "manager"},
            cookies={"v17_session": admin_token},
        )
        assert promote.status_code == 200
        assert promote.json()["updated_user"]["role"] == "manager"
        manager_token = second_body["session_token"]

        create_user = client.post(
            "/v17/auth/register",
            json={"username": "member", "password": "very-secure-pass", "display_name": "Member"},
        )
        member_id = int(create_user.json()["user"]["id"])

        manager_list = client.get("/v17/auth/users", cookies={"v17_session": manager_token})
        assert manager_list.status_code == 200

        manager_promote = client.post(
            f"/v17/auth/users/{member_id}/role",
            json={"role": "manager"},
            cookies={"v17_session": manager_token},
        )
        assert manager_promote.status_code == 200
        assert manager_promote.json()["updated_user"]["role"] == "manager"

        manager_to_admin = client.post(
            f"/v17/auth/users/{member_id}/role",
            json={"role": "admin"},
            cookies={"v17_session": manager_token},
        )
        assert manager_to_admin.status_code == 400

        promote_admin = client.post(
            f"/v17/auth/users/{operator_id}/role",
            json={"role": "admin"},
            cookies={"v17_session": admin_token},
        )
        assert promote_admin.status_code == 400


def test_stream_requires_authentication(isolated_auth_db) -> None:
    with TestClient(app) as client:
        r = client.post(
            "/v17/stream",
            json={"v17_origin": "v17_rebirth"},
            params={"birth_time": "1977-05-08T18:00:00", "gender": "male", "flow_year": 2026},
        )
        assert r.status_code == 401


def test_profile_crud_for_current_user(isolated_auth_db) -> None:
    with TestClient(app) as client:
        login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        token = login.json()["session_token"]
        cookies = {"v17_session": token}

        create_resp = client.post(
            "/v17/auth/profiles",
            cookies=cookies,
            json={
                "profile_name": "测试命盘",
                "birth_time_iso": "1990-01-01T00:00:00",
                "gender": "male",
                "calendar_type": "solar",
                "city_name": "北京市",
                "city_code": "110000",
                "city_group": "cn-direct-municipalities",
                "city_longitude": 116.4074,
            },
        )
        assert create_resp.status_code == 200
        created = create_resp.json()["profile"]
        assert created["profile_name"] == "测试命盘"
        assert created["birth_time_iso"] == "1990-01-01T00:00:00"
        assert created["city_name"] == "北京市"
        assert created["city_code"] == "110000"
        assert created["city_group"] == "cn-direct-municipalities"
        assert float(created["city_longitude"]) == pytest.approx(116.4074)
        profile_id = int(created["id"])

        list_resp = client.get("/v17/auth/profiles", cookies=cookies)
        assert list_resp.status_code == 200
        assert len(list_resp.json()["profiles"]) == 1

        update_resp = client.post(
            f"/v17/auth/profiles/{profile_id}",
            cookies=cookies,
            json={
                "profile_name": "测试命盘-更新",
                "birth_time_iso": "1990-01-01T00:30:00",
                "gender": "female",
                "calendar_type": "lunar",
                "city_name": "上海市",
                "city_code": "310000",
                "city_group": "cn-direct-municipalities",
                "city_longitude": 121.4737,
            },
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()["profile"]
        assert updated["profile_name"] == "测试命盘-更新"
        assert updated["birth_time_iso"] == "1990-01-01T00:30:00"
        assert updated["gender"] == "female"
        assert updated["calendar_type"] == "lunar"
        assert updated["city_name"] == "上海市"
        assert updated["city_code"] == "310000"
        assert updated["city_group"] == "cn-direct-municipalities"
        assert float(updated["city_longitude"]) == pytest.approx(121.4737)

        touch_resp = client.post(f"/v17/auth/profiles/{profile_id}/touch", cookies=cookies)
        assert touch_resp.status_code == 200
        assert touch_resp.json()["profile"]["last_used_at"]

        delete_resp = client.post(f"/v17/auth/profiles/{profile_id}/delete", cookies=cookies)
        assert delete_resp.status_code == 200

        list_after_delete = client.get("/v17/auth/profiles", cookies=cookies)
        assert list_after_delete.status_code == 200
        assert list_after_delete.json()["profiles"] == []


def test_practitioner_feedback_records_evidence_claim_and_role_weight(isolated_auth_db) -> None:
    with TestClient(app) as client:
        login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        token = login.json()["session_token"]
        cookies = {"v17_session": token}

        create_resp = client.post(
            "/v17/auth/practitioner-feedback",
            cookies=cookies,
            json={
                "session_id": "oracle-session-1",
                "evidence_id": "classical.pattern.yangren_jiasha.v1_evidence_0",
                "claim_id": "classical.pattern.yangren_jiasha.v1_claim_0",
                "plugin_id": "classical.pattern.yangren_jiasha.v1",
                "evidence_type": "pattern",
                "target_god": "七杀",
                "status": "confirm",
                "reason": "刃杀位置明确，候选可以保留。",
                "confidence": 0.9,
                "source_title": "阳刃驾杀",
                "source_summary": "阳刃驾杀候选：刃杀同见。",
                "chart_fingerprint": "fp-1",
                "payload": {"detail_keys": ["blade_branch"]},
            },
        )

        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body["trust_tier"] == "practitioner"
        feedback = body["feedback"]
        assert feedback["status"] == "confirm"
        assert feedback["reviewer_role"] == "admin"
        assert feedback["reviewer_weight"] > 2.0
        assert feedback["payload"]["detail_keys"] == ["blade_branch"]

        list_resp = client.get(
            "/v17/auth/practitioner-feedback?session_id=oracle-session-1",
            cookies=cookies,
        )
        assert list_resp.status_code == 200
        rows = list_resp.json()["feedback"]
        assert len(rows) == 1
        assert rows[0]["evidence_id"] == "classical.pattern.yangren_jiasha.v1_evidence_0"


def test_practitioner_feedback_scope_all_requires_manager(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]

        user_resp = client.post(
            "/v17/auth/register",
            json={"username": "feedback-user", "password": "very-secure-pass"},
        )
        user_token = user_resp.json()["session_token"]
        user_id = int(user_resp.json()["user"]["id"])

        create_resp = client.post(
            "/v17/auth/practitioner-feedback",
            cookies={"v17_session": user_token},
            json={
                "session_id": "s-user",
                "evidence_id": "e-user",
                "plugin_id": "classical.risk_matrix.v1",
                "status": "watch",
                "reason": "先观察。",
            },
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["trust_tier"] == "user"

        user_all = client.get(
            "/v17/auth/practitioner-feedback?scope=all",
            cookies={"v17_session": user_token},
        )
        assert user_all.status_code == 200
        assert len(user_all.json()["feedback"]) == 1

        promote = client.post(
            f"/v17/auth/users/{user_id}/role",
            json={"role": "manager"},
            cookies={"v17_session": admin_token},
        )
        assert promote.status_code == 200

        manager_all = client.get(
            "/v17/auth/practitioner-feedback?scope=all",
            cookies={"v17_session": user_token},
        )
        assert manager_all.status_code == 200
        assert len(manager_all.json()["feedback"]) == 1

        invalid = client.post(
            "/v17/auth/practitioner-feedback",
            cookies={"v17_session": user_token},
            json={"evidence_id": "e-invalid", "status": "maybe"},
        )
        assert invalid.status_code == 400


def test_practitioner_case_library_records_real_case_and_benchmark_seed(isolated_auth_db) -> None:
    with TestClient(app) as client:
        login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        token = login.json()["session_token"]
        cookies = {"v17_session": token}

        create_resp = client.post(
            "/v17/auth/practitioner-cases",
            cookies=cookies,
            json={
                "case_key": "real.audit.yangren_false_positive_19770508",
                "case_title": "羊刃误判审计样盘",
                "description": "用于验证无劫财/羊刃时不得输出羊刃格。",
                "birth_time_iso": "1977-05-08T17:30:00",
                "gender": "male",
                "calendar_type": "solar",
                "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
                "luck_pillar": "庚子",
                "flow_pillar": "戊申",
                "flow_year": 2028,
                "tags": ["羊刃误判", "格局审计"],
                "expected_patterns": ["不成立:阳刃驾杀"],
                "expected_use_gods": ["伤官", "七杀"],
                "expected_risks": ["羊刃误报"],
                "boundary_flags": ["无羊刃支", "无劫财根"],
                "failure_modes": ["false_yangren"],
                "expected_notes": "命理师确认：此盘没有羊刃，若系统输出阳刃驾杀应进入错判库。",
                "source_feedback_ids": ["classical.pattern.yangren_jiasha.v1_evidence_0"],
                "chart_fingerprint": "fp-yangren-false-positive",
                "status": "benchmark_candidate",
                "payload": {"source": "manual_audit"},
            },
        )

        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body["trust_tier"] == "practitioner"
        case = body["case"]
        assert case["status"] == "benchmark_candidate"
        assert case["owner_weight"] > 2.0
        assert case["four_pillars"]["day"] == "乙丑"
        assert case["boundary_flags"] == ["无羊刃支", "无劫财根"]
        assert case["source_feedback_ids"] == ["classical.pattern.yangren_jiasha.v1_evidence_0"]
        seed = body["benchmark_seed"]
        assert seed["case_id"] == "real.audit.yangren_false_positive_19770508"
        assert seed["four_pillars"]["month"] == "乙巳"
        assert "false_yangren" in seed["audit_focus"]
        assert seed["reviewer_note"].startswith("命理师确认")

        list_resp = client.get(
            "/v17/auth/practitioner-cases?scope=all&status=benchmark_candidate",
            cookies=cookies,
        )
        assert list_resp.status_code == 200
        rows = list_resp.json()["cases"]
        assert len(rows) == 1
        assert rows[0]["benchmark_seed"]["case_id"] == "real.audit.yangren_false_positive_19770508"

        duplicate = client.post(
            "/v17/auth/practitioner-cases",
            cookies=cookies,
            json={
                "case_key": "real.audit.yangren_false_positive_19770508",
                "case_title": "重复案例",
                "birth_time_iso": "1977-05-08T17:30:00",
                "gender": "male",
            },
        )
        assert duplicate.status_code == 400


def test_practitioner_case_scope_and_user_status_guard(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]

        user_resp = client.post(
            "/v17/auth/register",
            json={"username": "case-user", "password": "very-secure-pass"},
        )
        user_token = user_resp.json()["session_token"]

        create_resp = client.post(
            "/v17/auth/practitioner-cases",
            cookies={"v17_session": user_token},
            json={
                "case_key": "user.case.false_follow",
                "case_title": "假从边界样盘",
                "birth_time_iso": "1985-02-01T08:00:00",
                "gender": "female",
                "calendar_type": "solar",
                "status": "benchmark_candidate",
                "failure_modes": ["false_follow"],
            },
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["trust_tier"] == "user"
        assert create_resp.json()["case"]["status"] == "submitted"

        user_all = client.get(
            "/v17/auth/practitioner-cases?scope=all",
            cookies={"v17_session": user_token},
        )
        assert user_all.status_code == 200
        assert len(user_all.json()["cases"]) == 1

        admin_all = client.get(
            "/v17/auth/practitioner-cases?scope=all",
            cookies={"v17_session": admin_token},
        )
        assert admin_all.status_code == 200
        assert len(admin_all.json()["cases"]) == 1
        assert admin_all.json()["cases"][0]["owner_username"] == "case-user"
