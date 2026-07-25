from __future__ import annotations

from fastapi.testclient import TestClient

from product.app import PRODUCT_API_PREFIX, create_product_app
from product.product_store import MemoryProductStore, _deduplicate_profile_archive


def _register(client: TestClient, *, role: str = "member", email: str = "member@example.com") -> dict[str, object]:
    response = client.post(
        f"{PRODUCT_API_PREFIX}/auth/register",
        json={"display_name": "正式用户", "email": email, "password": "secure-pass-123", "role": role},
    )
    assert response.status_code == 200
    return response.json()["account"]


def _profile_payload(name: str = "我的八字") -> dict[str, object]:
    return {
        "birth_input": {
            "birth_input_id": "product.profile.input",
            "name": name,
            "gender": "unknown",
            "calendar_type": "solar",
            "birth_date": "1987-05-12",
            "birth_time": "18:00",
            "birth_location": "上海",
            "timezone": "Asia/Shanghai",
            "input_quality": "user_birth_profile",
        }
    }


def test_registration_login_cookie_session_and_logout() -> None:
    client = TestClient(create_product_app())
    account = _register(client)
    assert account["account_role"] == "member"
    assert "password" not in account
    assert client.get(f"{PRODUCT_API_PREFIX}/auth/me").status_code == 200
    assert client.post(f"{PRODUCT_API_PREFIX}/auth/logout").status_code == 200
    assert client.get(f"{PRODUCT_API_PREFIX}/auth/me").status_code == 401
    assert client.post(f"{PRODUCT_API_PREFIX}/auth/login", json={"email": "member@example.com", "password": "wrong"}).status_code == 401
    assert client.post(f"{PRODUCT_API_PREFIX}/auth/login", json={"email": "member@example.com", "password": "secure-pass-123"}).status_code == 200


def test_fixed_admin_is_not_available_through_public_registration() -> None:
    store = MemoryProductStore()
    first = store.ensure_admin_account(email="jerrydidi@gmail.com", password="abcd1235", display_name="DeepBazi Admin")
    second = store.ensure_admin_account(email="jerrydidi@gmail.com", password="abcd1235", display_name="DeepBazi Admin")
    assert first["user_id"] == second["user_id"] == "v50-admin-primary"
    client = TestClient(create_product_app(product_store=store))
    denied = client.post(
        f"{PRODUCT_API_PREFIX}/auth/register",
        json={"display_name": "Fake Admin", "email": "fake@example.com", "password": "secure-pass-123", "role": "admin"},
    )
    assert denied.status_code == 422
    login = client.post(f"{PRODUCT_API_PREFIX}/auth/login", json={"email": "jerrydidi@gmail.com", "password": "abcd1235"})
    assert login.status_code == 200
    assert login.json()["account"]["account_role"] == "admin"


def test_profile_crud_resolves_pillars_and_preserves_defaults() -> None:
    client = TestClient(create_product_app())
    _register(client)
    created = client.post(f"{PRODUCT_API_PREFIX}/profiles", json=_profile_payload())
    assert created.status_code == 200
    profile = created.json()["profile"]
    assert profile["pillars"] == ["丁卯", "乙巳", "辛酉", "丁酉"]
    assert profile["birth_location"] == "上海"
    detail = client.get(f"{PRODUCT_API_PREFIX}/profiles/{profile['profile_id']}")
    assert detail.status_code == 200
    assert detail.json()["profile"]["profile_id"] == profile["profile_id"]
    duplicate = client.post(f"{PRODUCT_API_PREFIX}/profiles", json=_profile_payload())
    assert duplicate.status_code == 200
    assert duplicate.json()["profile"]["profile_id"] == profile["profile_id"]
    same_birth_other_person = client.post(f"{PRODUCT_API_PREFIX}/profiles", json=_profile_payload("同一时辰的另一人"))
    assert same_birth_other_person.status_code == 200
    assert same_birth_other_person.json()["profile"]["profile_id"] != profile["profile_id"]
    listed = client.get(f"{PRODUCT_API_PREFIX}/profiles").json()["profiles"]
    assert {item["profile_id"] for item in listed} == {
        profile["profile_id"],
        same_birth_other_person.json()["profile"]["profile_id"],
    }
    updated = client.put(f"{PRODUCT_API_PREFIX}/profiles/{profile['profile_id']}", json=_profile_payload("更新后的档案"))
    assert updated.status_code == 200
    assert updated.json()["profile"]["display_name"] == "更新后的档案"
    assert client.delete(f"{PRODUCT_API_PREFIX}/profiles/{profile['profile_id']}").status_code == 200
    remaining = client.get(f"{PRODUCT_API_PREFIX}/profiles").json()["profiles"]
    assert [item["display_name"] for item in remaining] == ["同一时辰的另一人"]


def test_profile_archive_hides_legacy_retry_duplicates_without_hiding_twins() -> None:
    values = [
        {"profile_id": "new", "profile_fingerprint": "same-birth", "display_name": "同一人", "is_default": True},
        {"profile_id": "old", "profile_fingerprint": "same-birth", "display_name": "同一人", "is_default": False},
        {"profile_id": "twin", "profile_fingerprint": "same-birth", "display_name": "同一时辰的另一人", "is_default": False},
    ]
    assert [item["profile_id"] for item in _deduplicate_profile_archive(values)] == ["new", "twin"]


def test_profile_detail_is_private_and_missing_profile_is_explicit() -> None:
    client = TestClient(create_product_app())
    assert client.get(f"{PRODUCT_API_PREFIX}/profiles/unknown").status_code == 401
    _register(client)
    assert client.get(f"{PRODUCT_API_PREFIX}/profiles/unknown").status_code == 404


def test_abu_knows_a_confirmed_profile_does_not_need_birth_intake_again() -> None:
    client = TestClient(create_product_app())
    response = client.post(
        "/api/v50/agent/abu/resolve",
        json={
            "message": "开始看盘",
            "has_case": False,
            "has_profile": True,
            "active_mode": "member",
            "active_domain": "whole_chart",
        },
    )
    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["capability_id"] == "reading.start"
    assert "不再重复询问出生信息" in plan["abu_message"]
