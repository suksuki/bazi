from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "apps/product/static/l5/index.html"
CSS = ROOT / "apps/product/static/l5/styles.css"
JS = ROOT / "apps/product/static/l5/app.js"


def test_abu_companion_dock_has_three_surface_controls():
    html = HTML.read_text(encoding="utf-8")

    assert 'class="app-shell abu-panel-open"' in html
    assert 'id="abuStage" type="button"' in html
    assert 'aria-expanded="true"' in html
    assert 'id="abuPanelMinimize"' in html
    assert 'id="abuPeek"' in html
    assert 'id="abuPeekLabel"' in html
    assert 'id="abuPeekText"' in html
    assert 'id="abuPeekPreview"' in html
    assert 'id="abuPeekOpen"' in html
    assert 'id="abuPanelScrim"' in html
    assert "20260717-thinking-chart-v1" in html


def test_abu_surface_runtime_preserves_open_collapsed_preference_and_transient_peek():
    javascript = JS.read_text(encoding="utf-8")

    assert 'localStorage.getItem("deepbazi.abu_surface")' in javascript
    assert 'function initializeAbuSurface()' in javascript
    assert 'function setAbuSurface(surface' in javascript
    assert '["open", "peek", "collapsed"]' in javascript
    assert 'localStorage.setItem("deepbazi.abu_surface", next)' in javascript
    assert 'function showAbuPeek(message)' in javascript
    assert 'function setAbuLoadingPeek' in javascript
    assert 'abuPeekPinned: false' in javascript
    assert 'function compactAbuPeek(text)' in javascript
    assert 'setAbuSurface("collapsed")' in javascript
    assert 'setAbuSurface("open")' in javascript
    assert 'setAbuSurface("peek", { persist: false' in javascript
    assert 'if (type === "abu") showAbuPeek' in javascript


def test_loading_is_owned_by_the_floating_abu_instead_of_a_second_page_character():
    html = HTML.read_text(encoding="utf-8")
    javascript = JS.read_text(encoding="utf-8")

    assert 'class="thinking-abu-loader"' not in html
    assert 'class="thinking-atmosphere"' in html
    assert 'setAbuLoadingPeek(title, detail, progress);' in javascript
    assert 'const peek = el("abuPeekPreview")' in javascript
    assert 'panel.remove();' in javascript


def test_reading_canvas_owns_full_width_while_abu_floats_above_it():
    css = CSS.read_text(encoding="utf-8")

    assert "/* Abu Companion Dock v2" in css
    assert ".task-canvas {\n  display: block !important;\n  width: 100%;" in css
    assert ".conversation-pane {\n  position: fixed;" in css
    assert ".app-shell.abu-panel-collapsed .conversation-pane" in css


def test_abu_docks_left_and_opens_its_bubble_to_the_right_on_every_viewport():
    javascript = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    assert "/* Abu Companion Dock v2" in css
    assert "left: max(18px, env(safe-area-inset-left));" in css
    assert "left: max(10px, env(safe-area-inset-left));" in css
    assert ".app-shell.abu-panel-peek .abu-presence { left: 0; right: auto;" in css
    assert ".app-shell.abu-panel-peek .abu-peek { left: 92px; right: 0;" in css
    assert ".app-shell.abu-panel-peek .abu-peek::before { left: -7px; right: auto; transform: rotate(45deg); }" in css
    assert "return { left: 22, top: window.innerHeight - height - 22" in javascript
    assert ".app-shell.abu-panel-peek .abu-peek" in css
    assert ".app-shell.abu-panel-open .abu-panel-scrim" in css
    assert ".mobile-view-toggle { display: none !important; }" in css
    assert "height: min(76vh, 680px);" in css
    assert ".app-shell.abu-panel-peek .abu-peek { left: 0; right: 92px;" not in css
    assert ".app-shell.abu-panel-peek .abu-peek { right: 82px;" not in css


def test_welcome_narrative_balances_the_left_docked_abu():
    css = CSS.read_text(encoding="utf-8")

    welcome = css.split("/* Welcome composition v2", 1)[1]
    assert "@media (min-width: 961px)" in welcome
    assert "justify-content: flex-end;" in welcome
    assert "width: min(43vw, 570px);" in welcome
    assert "@media (max-width: 960px)" in welcome
    assert "align-items: flex-start;" in welcome
    assert "padding-top: clamp(36px, 7vh, 64px);" in welcome


def test_thinking_canvas_keeps_confirmed_chart_identity_visible():
    html = HTML.read_text(encoding="utf-8")
    javascript = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    assert 'id="thinkingChartContext"' in html
    assert 'id="thinkingProfileName"' in html
    assert 'id="thinkingProfileGender"' in html
    assert 'id="thinkingBirthMeta"' in html
    assert 'id="thinkingProfilePillars"' in html
    assert "function renderThinkingChartContext()" in javascript
    assert 'gender === "male" ? "乾造" : gender === "female" ? "坤造" : "命造"' in javascript
    assert 'if (event.event_type === "chart_ready") renderThinkingChartContext();' in javascript
    assert "renderPillarSet(pillars.filter(Boolean))" in javascript
    assert "/* Thinking chart identity v1" in css
    assert ".thinking-profile-pillars .mingli-pillars" in css


def test_mobile_uses_bottom_sheet_and_keeps_reading_canvas_visible():
    css = CSS.read_text(encoding="utf-8")

    mobile = css.split("/* Abu Companion Dock v2", 1)[1]
    assert "@media (max-width: 960px)" in mobile
    assert ".app-shell:not(.mobile-canvas) .task-canvas" in mobile
    assert ".app-shell.mobile-canvas .task-canvas { display: block !important; }" in mobile
    assert "bottom: max(8px, env(safe-area-inset-bottom));" in mobile
    assert "backdrop-filter: blur(2px);" in mobile
