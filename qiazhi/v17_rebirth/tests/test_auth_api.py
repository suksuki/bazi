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
        assert body["user"]["role"] == "practitioner"
        assert body["role_request"] is None

        token = body["session_token"]
        me = client.get("/v17/auth/me", cookies={"v17_session": token})
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["user"]["username"] == "founder"
        assert "oracle.access" in me_body["user"]["capabilities"]
        assert "oracle.simple" in me_body["user"]["capabilities"]
        assert "oracle.professional" in me_body["user"]["capabilities"]
        assert "practitioner.case.write" in me_body["user"]["capabilities"]
        assert me_body["user"]["surface_access"]["oracle"] == ["core", "auxiliary"]
        assert me_body["user"]["surface_access"]["admin"] is False


def test_practitioner_role_request_requires_manager_approval(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]

        applicant = isolated_auth_db.create_user(
            username="consultant",
            password="very-secure-pass",
            display_name="Consultant",
            role="user",
        )
        role_request = isolated_auth_db.create_role_request(
            user_id=int(applicant["id"]),
            requested_role="practitioner",
            reason="十年案例校验经验，愿意参与格局审计。",
        )
        login = client.post(
            "/v17/auth/login",
            json={"identifier": "consultant", "password": "very-secure-pass"},
        )
        applicant_token = login.json()["session_token"]
        applicant_id = int(applicant["id"])
        request_id = int(role_request["id"])

        before_me = client.get("/v17/auth/me", cookies={"v17_session": applicant_token})
        assert "oracle.professional" not in before_me.json()["user"]["capabilities"]

        requests = client.get(
            "/v17/auth/role-requests",
            cookies={"v17_session": admin_token},
        )
        assert requests.status_code == 200
        pending = requests.json()["role_requests"]
        assert any(row["id"] == request_id and row["username"] == "consultant" for row in pending)

        users = client.get("/v17/auth/users", cookies={"v17_session": admin_token})
        applicant_row = next(row for row in users.json()["users"] if row["id"] == applicant_id)
        assert applicant_row["role_request_status"] == "pending"
        assert applicant_row["role_request_role"] == "practitioner"

        approve = client.post(
            f"/v17/auth/role-requests/{request_id}/decision",
            json={"status": "approved", "reviewer_note": "通过测试审核"},
            cookies={"v17_session": admin_token},
        )
        assert approve.status_code == 200
        assert approve.json()["role_request"]["status"] == "approved"
        assert approve.json()["updated_user"]["role"] == "practitioner"

        after_me = client.get("/v17/auth/me", cookies={"v17_session": applicant_token})
        assert after_me.status_code == 200
        assert after_me.json()["user"]["role"] == "practitioner"
        assert "oracle.professional" in after_me.json()["user"]["capabilities"]
        assert "practitioner.case.write" in after_me.json()["user"]["capabilities"]

        feedback = client.post(
            "/v17/auth/practitioner-feedback",
            cookies={"v17_session": applicant_token},
            json={
                "session_id": "role-request-flow",
                "evidence_id": "pattern.yangren.audit",
                "claim_id": "claim-1",
                "plugin_id": "classical.ziping.pattern_bridge.v1",
                "status": "confirm",
                "reason": "此处证据链成立。",
                "confidence": 0.8,
                "source_title": "格局证据",
            },
        )
        assert feedback.status_code == 200

        case = client.post(
            "/v17/auth/practitioner-cases",
            cookies={"v17_session": applicant_token},
            json={
                "case_title": "命理师样盘",
                "birth_time_iso": "1990-01-01T00:00:00",
                "gender": "male",
                "calendar_type": "solar",
                "four_pillars": {"year": "庚午", "month": "戊子", "day": "乙亥", "hour": "丙子"},
                "expected_patterns": ["常规身弱"],
                "expected_notes": "用于验证贡献画像统计。",
                "status": "benchmark_candidate",
            },
        )
        assert case.status_code == 200

        users_after_contribution = client.get("/v17/auth/users", cookies={"v17_session": admin_token})
        contributor_row = next(row for row in users_after_contribution.json()["users"] if row["id"] == applicant_id)
        contribution = contributor_row["practitioner_contribution"]
        assert contribution["feedback_count"] == 1
        assert contribution["confirm_count"] == 1
        assert contribution["case_count"] == 1
        assert contribution["benchmark_count"] == 1
        assert contribution["score"] > 0
        assert contribution["tier"] in {"seed", "active", "anchor"}


def test_practitioner_evidence_review_is_trusted_review_only(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]
        isolated_auth_db.create_user(
            username="reviewer",
            password="very-secure-pass",
            display_name="Reviewer",
            role="user",
        )
        register = client.post(
            "/v17/auth/login",
            json={"identifier": "reviewer", "password": "very-secure-pass"},
        )
        user_token = register.json()["session_token"]
        user_id = int(register.json()["user"]["id"])

        payload = {
            "session_id": "evidence-review-flow",
            "chart_fingerprint": "fp-review",
            "summary": {"total": 2, "candidate_count": 1, "risk_count": 1, "observe_only_count": 1},
            "items": [
                {
                    "evidence_id": "ev-strong",
                    "claim_id": "claim-strong",
                    "title": "羊刃证据",
                    "summary": "羊刃与七杀同链。",
                    "source_plugin": "classical.pattern.yangren",
                    "evidence_type": "pattern",
                    "confidence": 0.82,
                    "match_ratio": 0.76,
                },
                {
                    "evidence_id": "ev-watch",
                    "title": "破格风险",
                    "source_plugin": "classical.risk.break_guard",
                    "evidence_type": "risk",
                    "confidence": 0.4,
                    "candidate_status": "watch",
                    "observe_only": True,
                },
            ],
        }

        denied = client.post(
            "/v17/auth/practitioner-evidence-review",
            cookies={"v17_session": user_token},
            json=payload,
        )
        assert denied.status_code == 403

        promote = client.post(
            f"/v17/auth/users/{user_id}/role",
            json={"role": "practitioner"},
            cookies={"v17_session": admin_token},
        )
        assert promote.status_code == 200

        review = client.post(
            "/v17/auth/practitioner-evidence-review",
            cookies={"v17_session": user_token},
            json=payload,
        )
        assert review.status_code == 200
        body = review.json()
        assert body["mode"] == "draft"
        assert body["safety_gate"] == "review_only"
        assert body["prompt_contract"]["task_type"] == "evidence_chain_review"
        assert body["prompt_contract"]["policy_version"] == "v17.evidence.review.v1.0"
        assert body["review"]["review_version"] == "v17.evidence.review.result.v1"
        assert body["review"]["summary"]["strong_count"] == 1
        assert body["review"]["summary"]["practitioner_review_required"] is False
        assert body["review"]["items"][1]["review_action"] == "keep_candidate"
        assert "observe_only" in body["review"]["items"][1]["risk_flags"]

        english_review = client.post(
            "/v17/auth/practitioner-evidence-review",
            cookies={"v17_session": user_token},
            json={**payload, "ui_lang": "en"},
        )
        assert english_review.status_code == 200
        english_body = english_review.json()
        assert english_body["prompt_contract"]["output_language"] == "en"
        assert english_body["prompt_contract"]["output_contract"]["reason_language"] == "en"
        assert "Output structured JSON only" in english_body["prompt_text"]
        assert "evidence is strong enough" in english_body["review"]["items"][0]["reason"]


def test_registered_user_defaults_to_practitioner_and_manager_can_promote_non_admin(isolated_auth_db) -> None:
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
        assert second_body["user"]["role"] == "practitioner"
        operator_id = int(second_body["user"]["id"])

        list_resp = client.get("/v17/auth/users", cookies={"v17_session": admin_token})
        assert list_resp.status_code == 200
        assert len(list_resp.json()["users"]) == 2
        operator_row = next(row for row in list_resp.json()["users"] if row["username"] == "operator")
        assert operator_row["latest_ip_address"] == "203.0.113.25"

        promote_practitioner = client.post(
            f"/v17/auth/users/{operator_id}/role",
            json={"role": "practitioner"},
            cookies={"v17_session": admin_token},
        )
        assert promote_practitioner.status_code == 200
        practitioner_user = promote_practitioner.json()["updated_user"]
        assert practitioner_user["role"] == "practitioner"
        assert "oracle.professional" in practitioner_user["capabilities"]
        assert "evidence.feedback.practitioner" in practitioner_user["capabilities"]
        assert practitioner_user["surface_access"]["oracle"] == ["core", "auxiliary"]

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
            json={"role": "practitioner"},
            cookies={"v17_session": manager_token},
        )
        assert manager_promote.status_code == 200
        assert manager_promote.json()["updated_user"]["role"] == "practitioner"

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

        isolated_auth_db.create_user(
            username="feedback-user",
            password="very-secure-pass",
            role="user",
        )
        user_resp = client.post(
            "/v17/auth/login",
            json={"identifier": "feedback-user", "password": "very-secure-pass"},
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
        assert create_resp.status_code == 403

        promote_practitioner = client.post(
            f"/v17/auth/users/{user_id}/role",
            json={"role": "practitioner"},
            cookies={"v17_session": admin_token},
        )
        assert promote_practitioner.status_code == 200

        create_resp = client.post(
            "/v17/auth/practitioner-feedback",
            cookies={"v17_session": user_token},
            json={
                "session_id": "s-user",
                "evidence_id": "e-user",
                "plugin_id": "classical.risk_matrix.v1",
                "status": "watch",
                "reason": "先观察。",
                "confidence": 0.8,
            },
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["trust_tier"] == "practitioner"
        assert create_resp.json()["feedback"]["reviewer_role"] == "practitioner"
        assert create_resp.json()["feedback"]["reviewer_weight"] == pytest.approx(2.0)

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

        accept_resp = client.post(
            f"/v17/auth/practitioner-cases/{case['id']}/status",
            cookies=cookies,
            json={
                "status": "accepted",
                "reviewer_note": "纳入长期 Practitioner Benchmark 候选池。",
            },
        )
        assert accept_resp.status_code == 200
        accept_body = accept_resp.json()
        assert accept_body["case"]["status"] == "accepted"
        assert accept_body["applied_to_static_benchmark"] is False
        assert accept_body["guardrail"] == "case_status_only_no_test_file_change"
        assert accept_body["case"]["payload"]["status_reviewer_note"].startswith("纳入长期")

        accepted_list = client.get(
            "/v17/auth/practitioner-cases?scope=all&status=accepted",
            cookies=cookies,
        )
        assert accepted_list.status_code == 200
        assert len(accepted_list.json()["cases"]) == 1

        export_resp = client.get(
            "/v17/auth/practitioner-benchmark-export",
            cookies=cookies,
        )
        assert export_resp.status_code == 200
        export_body = export_resp.json()
        assert export_body["protocol"] == "v17.practitioner.benchmark_export.v1"
        assert export_body["summary"]["accepted_case_count"] == 1
        assert export_body["benchmark_cases"][0]["case_id"] == "real.audit.yangren_false_positive_19770508"
        assert "PractitionerBenchmarkCase" in export_body["python_case_snippets"][0]
        assert "PRACTITIONER_ACCEPTED_REAL_AUDIT_YANGREN_FALSE_POSITIVE_19770508" in export_body["python_registry_snippet"]
        assert export_body["guardrails"][0] == "export is read-only"

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

        isolated_auth_db.create_user(
            username="case-user",
            password="very-secure-pass",
            role="user",
        )
        user_resp = client.post(
            "/v17/auth/login",
            json={"identifier": "case-user", "password": "very-secure-pass"},
        )
        user_token = user_resp.json()["session_token"]
        user_id = int(user_resp.json()["user"]["id"])

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
        assert create_resp.status_code == 403

        promote_practitioner = client.post(
            f"/v17/auth/users/{user_id}/role",
            json={"role": "practitioner"},
            cookies={"v17_session": admin_token},
        )
        assert promote_practitioner.status_code == 200

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
        assert create_resp.json()["trust_tier"] == "practitioner"
        assert create_resp.json()["case"]["status"] == "benchmark_candidate"
        assert create_resp.json()["case"]["owner_role"] == "practitioner"
        assert create_resp.json()["case"]["owner_weight"] == pytest.approx(2.0)

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


def test_practitioner_learning_candidates_summarize_feedback_and_cases(isolated_auth_db) -> None:
    with TestClient(app) as client:
        admin_login = client.post(
            "/v17/auth/login",
            json={"identifier": "admin", "password": "abcd1235"},
        )
        admin_token = admin_login.json()["session_token"]

        user_resp = client.post(
            "/v17/auth/register",
            json={"username": "candidate-user", "password": "very-secure-pass"},
        )
        user_token = user_resp.json()["session_token"]

        initial_own = client.get(
            "/v17/auth/practitioner-learning-candidates",
            cookies={"v17_session": user_token},
        )
        assert initial_own.status_code == 200
        assert initial_own.json()["scope"] == "own"

        feedback_resp = client.post(
            "/v17/auth/practitioner-feedback",
            cookies={"v17_session": user_token},
            json={
                "session_id": "s-candidate",
                "evidence_id": "classical.pattern.yangren_jiasha.v1_evidence_false_positive",
                "claim_id": "classical.pattern.yangren_jiasha.v1_claim_false_positive",
                "plugin_id": "classical.pattern.yangren_jiasha.v1",
                "evidence_type": "pattern",
                "status": "reject",
                "reason": "此盘没有羊刃，也没有劫财根，阳刃驾杀应判为误报。",
                "confidence": 0.95,
                "source_title": "阳刃驾杀",
                "source_summary": "候选误报。",
                "chart_fingerprint": "fp-learning-yangren",
                "payload": {
                    "material_protocol": "v17.evidence.learning_material.v1",
                    "failure_mode": "false_yangren",
                    "feedback_intent": "false_positive_or_wrong_claim",
                    "learning_value": "counterexample",
                    "learning_tags": ["needs_counterexample", "evidence_type:pattern"],
                    "boundary_tags": ["无羊刃支"],
                },
            },
        )
        assert feedback_resp.status_code == 200

        case_resp = client.post(
            "/v17/auth/practitioner-cases",
            cookies={"v17_session": user_token},
            json={
                "case_key": "learning.false_yangren.19770508",
                "case_title": "羊刃误判学习候选",
                "birth_time_iso": "1977-05-08T17:30:00",
                "gender": "male",
                "calendar_type": "solar",
                "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
                "tags": ["羊刃误判", "格局审计"],
                "expected_patterns": ["不成立:阳刃驾杀"],
                "boundary_flags": ["无羊刃支", "无劫财根"],
                "failure_modes": ["false_yangren"],
                "expected_notes": "用于学习候选，不允许直接调参。",
                "source_feedback_ids": ["classical.pattern.yangren_jiasha.v1_evidence_false_positive"],
                "chart_fingerprint": "fp-learning-yangren",
                "status": "benchmark_candidate",
                "payload": {
                    "material_protocol": "v17.evidence.learning_material.v1",
                    "learning_value": "counterexample",
                    "learning_tags": ["benchmark_candidate", "source:practitioner_case"],
                },
            },
        )
        assert case_resp.status_code == 200

        own_report = client.get(
            "/v17/auth/practitioner-learning-candidates",
            cookies={"v17_session": user_token},
        )
        assert own_report.status_code == 200
        body = own_report.json()
        assert body["protocol"] == "v17.practitioner.learning_candidates.v1"
        assert body["scope"] == "own"
        assert body["summary"]["learning_loop_state"] == "review_candidates_ready"
        assert body["summary"]["manual_review_required_count"] == 1
        candidate = body["candidates"][0]
        assert candidate["parameter_family"] == "pattern_specialization.yangren_gate"
        assert candidate["safety_gate"] == "manual_review_required"
        assert candidate["recommended_action"] == "review_classical_pattern_gate"
        assert candidate["reject_count"] == 1
        assert candidate["benchmark_candidate_count"] == 1
        assert candidate["trusted_contributor_count"] == 2
        assert candidate["contributor_reputation_score"] > 0
        assert "seed" in candidate["contributor_tiers"]
        assert candidate["priority"] == "high"
        assert "classical.pattern.yangren_jiasha.v1" in candidate["source_plugins"]
        assert "learning.false_yangren.19770508" in candidate["source_cases"]
        assert "counterexample" in candidate["learning_values"]
        assert "false_positive_or_wrong_claim" in candidate["feedback_intents"]
        assert "needs_counterexample" in candidate["learning_tags"]
        assert "无羊刃支" in candidate["boundary_tags"]
        assert any("羊刃" in hint for hint in candidate["review_hints"])

        admin_all = client.get(
            "/v17/auth/practitioner-learning-candidates?scope=all",
            cookies={"v17_session": admin_token},
        )
        assert admin_all.status_code == 200
        assert admin_all.json()["scope"] == "all"
        assert admin_all.json()["summary"]["candidate_count"] == 1

        practitioner_review = client.post(
            "/v17/auth/practitioner-learning-reviews",
            cookies={"v17_session": user_token},
            json={
                "candidate_id": candidate["candidate_id"],
                "parameter_family": candidate["parameter_family"],
                "status": "approved_for_experiment",
            },
        )
        assert practitioner_review.status_code == 403

        review_resp = client.post(
            "/v17/auth/practitioner-learning-reviews",
            cookies={"v17_session": admin_token},
            json={
                "candidate_id": candidate["candidate_id"],
                "parameter_family": candidate["parameter_family"],
                "status": "approved_for_experiment",
                "reviewer_note": "允许进入 synthetic shadow run，不允许直接改线上参数。",
                "candidate_snapshot": candidate,
            },
        )
        assert review_resp.status_code == 200
        review_body = review_resp.json()
        assert review_body["applied"] is False
        assert review_body["guardrail"] == "review_only_no_runtime_parameter_change"
        assert review_body["review"]["status"] == "approved_for_experiment"

        reviews = client.get(
            f"/v17/auth/practitioner-learning-reviews?candidate_id={candidate['candidate_id']}",
            cookies={"v17_session": admin_token},
        )
        assert reviews.status_code == 200
        assert len(reviews.json()["reviews"]) == 1

        reviewed_report = client.get(
            "/v17/auth/practitioner-learning-candidates?scope=all",
            cookies={"v17_session": admin_token},
        )
        reviewed_candidate = reviewed_report.json()["candidates"][0]
        assert reviewed_candidate["review_status"] == "approved_for_experiment"
        assert reviewed_candidate["review_count"] == 1
        assert reviewed_candidate["latest_review"]["reviewer_note"].startswith("允许进入 synthetic")

        experiments = client.get(
            "/v17/auth/practitioner-learning-experiments",
            cookies={"v17_session": admin_token},
        )
        assert experiments.status_code == 200
        experiment_body = experiments.json()
        assert experiment_body["protocol"] == "v17.practitioner.experiment_queue.v1"
        assert experiment_body["state"] == "ready_for_shadow_run"
        assert experiment_body["experiment_count"] == 1
        experiment = experiment_body["experiments"][0]
        assert experiment["candidate_id"] == candidate["candidate_id"]
        assert experiment["application_mode"] == "dry_run_plan_only"
        assert experiment["candidate_patch"]["patch_mode"] == "review_only"
        assert "rollback_plan_required_before_apply" in experiment["safety_gates"]

        release_without_scorecard = client.post(
            "/v17/auth/practitioner-learning-releases",
            cookies={"v17_session": admin_token},
            json={
                "experiment_id": experiment["experiment_id"],
                "candidate_id": experiment["candidate_id"],
                "parameter_family": experiment["parameter_family"],
                "status": "approved",
                "release_summary": "不能绕过 scorecard。",
                "test_report": "synthetic + practitioner benchmark passed",
                "rollback_plan": "恢复上一版参数。",
            },
        )
        assert release_without_scorecard.status_code == 400
        assert "promote scorecard" in release_without_scorecard.json()["detail"]

        bad_scorecard = client.post(
            "/v17/auth/practitioner-learning-scorecards",
            cookies={"v17_session": admin_token},
            json={
                "experiment_id": experiment["experiment_id"],
                "candidate_id": experiment["candidate_id"],
                "parameter_family": experiment["parameter_family"],
                "synthetic_passed": True,
                "practitioner_passed": False,
                "regression_count": 0,
                "verdict": "promote",
                "summary": "缺少 practitioner benchmark 通过，不应建议发布。",
            },
        )
        assert bad_scorecard.status_code == 400

        scorecard_resp = client.post(
            "/v17/auth/practitioner-learning-scorecards",
            cookies={"v17_session": admin_token},
            json={
                "experiment_id": experiment["experiment_id"],
                "candidate_id": experiment["candidate_id"],
                "parameter_family": experiment["parameter_family"],
                "synthetic_passed": True,
                "practitioner_passed": True,
                "improvement_count": 2,
                "regression_count": 0,
                "verdict": "promote",
                "summary": "shadow run 通过，可进入发布审批记录。",
                "experiment_snapshot": experiment,
                "payload": {"commands": experiment["required_commands"]},
            },
        )
        assert scorecard_resp.status_code == 200
        assert scorecard_resp.json()["applied"] is False
        assert scorecard_resp.json()["guardrail"] == "scorecard_record_only_no_config_change"
        assert scorecard_resp.json()["scorecard"]["verdict"] == "promote"

        scorecards = client.get(
            f"/v17/auth/practitioner-learning-scorecards?experiment_id={experiment['experiment_id']}",
            cookies={"v17_session": admin_token},
        )
        assert scorecards.status_code == 200
        assert len(scorecards.json()["scorecards"]) == 1

        bad_release = client.post(
            "/v17/auth/practitioner-learning-releases",
            cookies={"v17_session": admin_token},
            json={
                "experiment_id": experiment["experiment_id"],
                "candidate_id": experiment["candidate_id"],
                "parameter_family": experiment["parameter_family"],
                "status": "approved",
                "release_summary": "尝试缺少回滚方案的发布。",
                "test_report": "synthetic + practitioner benchmark passed",
            },
        )
        assert bad_release.status_code == 400

        release_resp = client.post(
            "/v17/auth/practitioner-learning-releases",
            cookies={"v17_session": admin_token},
            json={
                "experiment_id": experiment["experiment_id"],
                "candidate_id": experiment["candidate_id"],
                "parameter_family": experiment["parameter_family"],
                "status": "approved",
                "release_summary": "仅记录发布审批，仍不自动写配置。",
                "test_report": "synthetic + practitioner benchmark passed",
                "rollback_plan": "保留旧配置，失败时恢复上一版参数并重跑 benchmark。",
                "experiment_snapshot": experiment,
            },
        )
        assert release_resp.status_code == 200
        release_body = release_resp.json()
        assert release_body["applied"] is False
        assert release_body["guardrail"] == "release_record_only_no_config_change"
        assert release_body["release"]["status"] == "approved"
        assert release_body["release"]["applied"] is False

        releases = client.get(
            f"/v17/auth/practitioner-learning-releases?experiment_id={experiment['experiment_id']}",
            cookies={"v17_session": admin_token},
        )
        assert releases.status_code == 200
        assert len(releases.json()["releases"]) == 1

        export_resp = client.get(
            "/v17/auth/practitioner-learning-governance-export",
            cookies={"v17_session": admin_token},
        )
        assert export_resp.status_code == 200
        export_body = export_resp.json()
        assert export_body["protocol"] == "v17.practitioner.learning_governance_export.v1"
        assert export_body["summary"]["candidate_count"] == 1
        assert export_body["summary"]["review_count"] >= 1
        assert export_body["summary"]["experiment_count"] == 1
        assert export_body["summary"]["scorecard_count"] == 1
        assert export_body["summary"]["release_count"] == 1
        assert export_body["releases"][0]["experiment_id"] == experiment["experiment_id"]
