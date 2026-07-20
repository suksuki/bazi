from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "apps/product/static/l5/index.html"
APP = ROOT / "apps/product/static/l5/app.js"
MOTION_REGISTRY = ROOT / "apps/product/static/l5/assets/abu/motion-registry.js"
STYLES = ROOT / "apps/product/static/l5/styles.css"
CONTRACT = ROOT / "docs/product/V50_ABU_PERSONA_GUIDANCE_AND_MOTION_V1.md"


def test_abu_persona_is_visible_without_replacing_standard_product_language() -> None:
    index = INDEX.read_text(encoding="utf-8")
    javascript = APP.read_text(encoding="utf-8")

    assert "柴犬命理师" in index
    assert "先看见命局" in index
    assert "命理档案" in index
    assert "登录" in index
    assert "汪！" not in index
    assert "缘分锦囊" not in index
    assert "流年密档" not in index
    assert "我不会猜测缺失信息" in javascript


def test_abu_guidance_uses_journey_states_and_preserves_birth_time_uncertainty() -> None:
    index = INDEX.read_text(encoding="utf-8")
    javascript = APP.read_text(encoding="utf-8")
    motion_registry = MOTION_REGISTRY.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    for state in ("welcome", "listening", "parsing", "confirming", "thinking", "probe", "completed", "boundary"):
        assert f'{state}: "' in motion_registry

    assert 'name="time_precision"' in index
    assert 'value="approximate"' in index
    assert 'warnings: draft.time_precision === "exact" ? [] : ["birth_time_approximate"]' in javascript
    assert "大约值，将保留不确定性" in javascript
    assert 'data-state="listening"' in styles
    assert 'data-state="confirming"' in styles
    assert 'data-state="boundary"' in styles


def test_abu_contract_freezes_agent_and_action_boundaries() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "Abu is not a decorative mascot" in contract
    assert "Journey Runtime chooses the authorized next action" in contract
    assert "abu_creates_mingli_claim: false" in contract
    assert "birth_confirmation_required_before_compute: true" in contract
    assert "approximate_time_remains_approximate: true" in contract
