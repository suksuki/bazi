from fastapi.testclient import TestClient

from product.app import create_product_app
from product.product_store import MemoryProductStore


def test_reading_canvas_distinguishes_public_and_professional_modes() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    html = client.get("/app").text
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    assert "20260717-thinking-chart-v1" in html
    assert 'el("readingCanvas").dataset.mode = state.activeMode;' in js
    assert 'el("artifactContent").dataset.view' in js
    assert '.reading-canvas[data-mode="practitioner"]' in css
    assert '.reading-canvas[data-mode="research"]' in css
    assert "Reading Horizon & Deliberation Atelier v2" in css
    assert "Public Story Journey & Abu Loading Bubble v1" in css
    assert "function decoratePublicArtifact()" in js


def test_public_story_layout_uses_one_journey_and_contextual_detail_navigation() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    assert "Public Reading Story Layout v2" in css
    assert 'el("readingTabs").hidden = publicMode;' in js
    assert 'el("readingHeader").hidden = publicMode && overview;' in js
    assert 'el("readingBackButton").dataset.target = domainSelected ? "domains" : "overview";' in js
    assert ".reading-canvas.public-detail-view .reading-header" in css
    assert "function applyStoryDisclosure(artifact)" in js
    assert "function wrapStoryBandAsJourneyStep" not in js
    assert "applyStoryDisclosure(artifact)" in js
    assert "function typePrimaryReading(artifact)" in js
    assert 'artifact.classList.toggle("task-choice-artifact"' in js
    assert 'el("taskCanvas").scrollTop = 0;' in js


def test_public_domain_reading_is_a_three_step_journey_instead_of_a_long_report() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text

    domain_renderer = js.split("function renderDomainExploration(domain)", maxsplit=1)[1].split(
        "function renderDomainMap()", maxsplit=1
    )[0]
    public_domain_renderer = domain_renderer.split("if (publicMode)", maxsplit=1)[1].split(
        'const professional = ["practitioner", "research"].includes(state.activeMode)', maxsplit=1
    )[0]
    assert 'title: "核心判断"' in public_domain_renderer
    assert 'title: "何时成立，何时受阻"' in public_domain_renderer
    assert 'title: "现实方向"' in public_domain_renderer
    assert public_domain_renderer.count("renderJourneyStep({") == 3


def test_four_pillars_expose_stems_branches_hidden_stems_and_five_element_classes() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    assert "function renderPillarSet(pillars = [])" in js
    assert '"辰": { element: "earth", polarity: "yang", nature: "阳土", hidden: ["戊", "乙", "癸"] }' in js
    assert 'class="pillar-glyph pillar-stem element-${stemMeta.element}' in js
    assert 'class="hidden-stems"' in js
    assert ".mingli-pillars" in css
    assert ".element-wood" in css
    assert ".element-fire" in css
    assert ".element-earth" in css
    assert ".element-metal" in css
    assert ".element-water" in css


def test_professional_progress_is_readable_instead_of_a_bare_fraction() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    assert 'class="deliberation-progress" aria-label="已完成 ${completed} 个，共 ${total} 个研判步骤"' in js
    assert 'class="deliberation-progress-track"' in js
    assert 'String(index + 1).padStart(2, "0")' in js
    assert ".deliberation-stage-nav b" in css


def test_public_overview_leads_with_the_reading_and_collapses_revision_detail() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    member_renderer = js.split("function renderMemberOverview", maxsplit=1)[1].split("function renderHypothesis", maxsplit=1)[0]
    assert member_renderer.index('id: "baseline"') < member_renderer.index("renderLatestRevision(r)")
    assert 'class="case-revision compact-revision"' in js
    assert '.artifact[data-view="overview"][data-mode="member"]' in css
    assert "--reading-title-size:" in css


def test_public_overview_uses_single_open_accordion_with_explicit_tone_contrast() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    js = client.get("/app.js").text
    css = client.get("/styles.css").text

    assert "function renderJourneyStep" in js
    assert "function applyJourneyAccordion" in js
    assert 'data-journey-step="${escapeAttr(id)}"' in js
    assert 'aria-controls="${escapeAttr(bodyId)}"' in js
    assert 'state.journeyExpandedSteps[key] === selected ? "" : selected' in js
    assert ".journey-step.is-expanded .journey-step-body" in css
    assert ".public-story-artifact > .journey-step.story-dusk" in css
    assert ".domain-guidance-compact" in css
    assert "background-color: #3f5f53" in css
    assert "color: #fffaf0" in css
