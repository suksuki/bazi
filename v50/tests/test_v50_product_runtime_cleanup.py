from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from product.app import create_product_app
from product.product_store import MemoryProductStore
from core.life_domains import DOMAIN_PROTOCOLS, DOMAIN_REGISTRY, DomainReadiness, LifeDomain, domain_definition


def test_product_runtime_exposes_only_agent_account_profile_and_assets() -> None:
    app = create_product_app(product_store=MemoryProductStore())
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v50/agent/cases" in paths
    assert "/api/v50/product/profiles" in paths
    assert not any(path.startswith("/api/v50/alpha") for path in paths)
    assert "/visual-alpha/pro" not in paths
    assert "/visual-alpha/research" not in paths
    assert "/visual-alpha/debug" not in paths
    assert "/abu-motion" not in paths
    assert "/abu-motion.css" not in paths
    assert "/abu-motion.js" not in paths


def test_product_entry_keeps_theater_and_app_is_only_a_workspace_redirect() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    root = client.get("/", follow_redirects=False)
    assert root.status_code == 307
    assert root.headers["location"] == "/abu-theater"

    product = client.get("/app", follow_redirects=False)
    assert product.status_code == 308
    assert product.headers["location"] == "/experience"
    manage = client.get("/app?manage=1", follow_redirects=False)
    assert manage.headers["location"] == "/experience?manage=1"
    profile = client.get("/app?profile=profile-1", follow_redirects=False)
    assert profile.headers["location"] == "/experience?profile=profile-1"
    assert client.get("/app.js").status_code == 404
    assert client.get("/styles.css").status_code == 404
    assert client.get("/visual-alpha").status_code == 404
    assert client.get("/assets/deepbazi_symbol.png").status_code == 200
    assert client.get("/favicon.ico").status_code == 200
    assert client.get("/assets/valley_sunrise.jpg").status_code == 200
    assert client.get("/abu-motion").status_code == 404
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["product"] == "deepbazi_v50"


def test_unified_workspace_owns_auth_profiles_and_non_blocking_cognition() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/experience").text
    javascript = client.get("/experience-static/app.js").text
    stylesheet = client.get("/experience-static/styles.css").text

    assert "/experience-static/app.js" in html
    assert "/api/v50/product/auth/${input.mode}" in javascript
    assert "/api/v50/product/profiles" in javascript
    account_source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/account_components.ts"
    ).read_text(encoding="utf-8")
    assert "选择档案，就是进入命局" in account_source
    assert "startMissingBaseline(activeCaseId)" in javascript
    assert "最终事实与证据检查没有通过" not in javascript
    assert "重新看盘" not in javascript
    assert ".profile-manager" in stylesheet
    assert ".account-entry" in stylesheet


def test_life_domain_space_is_complete_and_exposes_readiness_boundaries() -> None:
    assert len(DOMAIN_REGISTRY) == 12
    assert {item.domain for item in DOMAIN_REGISTRY} == set(LifeDomain)
    assert domain_definition(LifeDomain.CAREER).publicly_available is True
    assert domain_definition(LifeDomain.WEALTH).publicly_available is True
    assert domain_definition(LifeDomain.RELATIONSHIP).readiness is DomainReadiness.RESEARCH
    assert domain_definition(LifeDomain.RELATIONSHIP).publicly_available is False
    assert {
        item.domain for item in DOMAIN_REGISTRY if item.publicly_available
    } == {
        LifeDomain.WHOLE_CHART,
        LifeDomain.CAREER,
        LifeDomain.WEALTH,
    }
    assert domain_definition(LifeDomain.RELATIONSHIP).boundary
    assert domain_definition(LifeDomain.HEALTH_VITALITY).boundary


def test_abu_recognizes_full_domain_space_and_states_boundaries() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    relationship = client.post(
        "/api/v50/agent/abu/resolve",
        json={"message": "我想看感情和婚姻", "has_case": True, "active_mode": "member", "active_domain": "whole_chart"},
    )
    assert relationship.status_code == 200
    plan = relationship.json()["plan"]
    assert plan["slots"]["domain"] == "relationship"
    assert "还没有达到可以负责任公开断言" in plan["abu_message"]
    assert plan["missing_requirements"] == ["capability_boundary"]
    assert plan["capability_id"] == "reading.select_domain"

    timing = client.post(
        "/api/v50/agent/abu/resolve",
        json={"message": "我现在处于什么人生阶段", "has_case": True, "active_mode": "member", "active_domain": "whole_chart"},
    ).json()["plan"]
    assert timing["slots"]["domain"] == "life_timing"
    assert timing["missing_requirements"] == ["capability_boundary"]


def test_every_specialized_life_domain_has_a_distinct_reasoning_and_probe_protocol() -> None:
    specialized = set(LifeDomain) - {LifeDomain.WHOLE_CHART}
    assert set(DOMAIN_PROTOCOLS) == specialized
    assert all(protocol.core_questions for protocol in DOMAIN_PROTOCOLS.values())
    assert len({protocol.probe_goal for protocol in DOMAIN_PROTOCOLS.values()}) == len(specialized)
    assert "疾病诊断" in DOMAIN_PROTOCOLS[LifeDomain.HEALTH_VITALITY].forbidden_claims


def test_professional_deliberation_api_remains_available_without_legacy_ui_owner() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    paths = {getattr(route, "path", "") for route in client.app.routes}
    assert "/api/v50/agent/cases/{case_id}/deliberation/select" in paths
    assert "/api/v50/agent/cases/{case_id}/deliberation/undo" in paths
    assert "/app.js" not in paths
    assert "/styles.css" not in paths
