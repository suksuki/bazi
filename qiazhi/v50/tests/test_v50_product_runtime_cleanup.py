from __future__ import annotations

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


def test_product_entry_uses_theater_and_app_keeps_formal_asset_routes() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    root = client.get("/", follow_redirects=False)
    assert root.status_code == 307
    assert root.headers["location"] == "/abu-theater"

    product = client.get("/app")
    assert product.status_code == 200
    assert "/styles.css" in product.text
    assert "/app.js" in product.text
    assert "/assets/abu/" in product.text
    assert "/assets/deepbazi_symbol.png" in product.text
    assert "/brand-assets/" not in product.text
    assert client.get("/assets/deepbazi_symbol.png").status_code == 200
    assert client.get("/favicon.ico").status_code == 200
    assert client.get("/assets/valley_sunrise.jpg").status_code == 200
    assert client.get("/abu-motion").status_code == 404
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["product"] == "deepbazi_v50"
    legacy = client.get("/visual-alpha", follow_redirects=False)
    assert legacy.status_code == 308
    assert legacy.headers["location"] == "/app"


def test_public_ui_turns_cognitive_failure_into_a_terminal_retry_surface() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    js = client.get("/app.js").text
    assert 'id="failureScene"' in html
    assert 'id="retryReadingButton"' in html
    assert "showCognitionFailure(payload)" in js
    assert 'runtime_recovery: "上一次看盘被服务中断"' in js


def test_public_ui_streams_accepted_mingli_artifacts_instead_of_only_progress_copy() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    js = client.get("/app.js").text
    css = client.get("/styles.css").text
    assert "20260717-thinking-chart-v1" in html
    assert "function renderProgressiveCanvas()" in js
    assert "pattern.first_look" in js
    assert "work.work_path?.path_statement" in js
    assert "dual.integrated_thesis" in js
    assert "predictions.prior_predictions" in js
    assert "第一眼已经形成，我先把它交给你" in js
    assert "function showThinkingPreviewLine" in js
    assert "pattern_preview_ready" in js
    assert "function updateThinkingPreview(text)" in js
    assert 'id="thinkingPreview"' in html
    assert 'id="abuPeekPreview"' in html
    assert "function setAbuLoadingPeek" in js
    assert ".abu-peek-copy" in css
    assert ".newly-accepted" in css


def test_public_ui_recovers_completed_reading_when_job_polling_or_restore_is_interrupted() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    assert 'const recovered = await restoreCase(state.caseId, true);' in js
    assert 'terminalStatus === "completed" && !state.reading' in js
    assert 'if (error.status === 404) localStorage.removeItem("deepbazi.case_id")' in js
    assert 'if (!caseId) return false;' in js


def test_public_ui_keeps_abu_case_and_profile_archive_in_one_state_chain() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    js = client.get("/app.js").text
    css = client.get("/styles.css").text
    assert 'id="birthDialogTitle"' in html
    assert "has_profile: Boolean(state.activeProfile)" in js
    assert "async function refreshProfiles" in js
    assert "function syncActiveProfile" in js
    assert "async function saveProfileFromDialog" in js
    assert "async function useProfileForReading" in js
    assert "async function deleteProfile" in js
    assert "case_context" in js
    assert ".profile-archive-card" in css


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
        LifeDomain.LIFE_TIMING,
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


def test_every_specialized_life_domain_has_a_distinct_reasoning_and_probe_protocol() -> None:
    specialized = set(LifeDomain) - {LifeDomain.WHOLE_CHART}
    assert set(DOMAIN_PROTOCOLS) == specialized
    assert all(protocol.core_questions for protocol in DOMAIN_PROTOCOLS.values())
    assert len({protocol.probe_goal for protocol in DOMAIN_PROTOCOLS.values()}) == len(specialized)
    assert "疾病诊断" in DOMAIN_PROTOCOLS[LifeDomain.HEALTH_VITALITY].forbidden_claims


def test_public_ui_uses_one_life_map_instead_of_fixed_career_wealth_tabs() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    js = client.get("/app.js").text
    assert 'data-artifact="domains"' in html
    assert 'data-artifact="career"' not in html
    assert 'data-artifact="wealth"' not in html
    assert "/domains/${domain}" in js
    assert "沿着整盘主线进入这个人生问题" in js
    assert 'const peek = el("abuPeekPreview")' in js


def test_public_reading_projection_hides_research_and_engine_language_by_active_mode() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    assert 'const professionalMode = ["practitioner", "research"].includes(state.activeMode)' in js
    assert 'state.activeMode === "research" && exploration?.review' in js
    assert 'probeHeading(state.activeMode)' in js
    assert 'slice(0, publicMode ? 2 : 3)' in js
    assert '查看专业依据与审阅' not in js


def test_professional_ui_exposes_guided_deliberation_without_global_mutation_controls() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    paths = {getattr(route, "path", "") for route in client.app.routes}
    js = client.get("/app.js").text
    assert "/api/v50/agent/cases/{case_id}/deliberation/select" in paths
    assert "/api/v50/agent/cases/{case_id}/deliberation/undo" in paths
    assert "专业研判工作台" in js
    assert "支持度表示当前案例候选之间的相对解释力" not in js
    assert "支持度、原始命盘和系统理论" not in js
    assert "Admin 页面预览" in js
