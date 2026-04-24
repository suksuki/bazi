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
