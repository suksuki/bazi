from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOTION_REGISTRY = ROOT / "apps/product/static/l5/assets/abu/motion-registry.js"
CONTRACT = ROOT / "docs/product/V50_ABU_PERSONA_GUIDANCE_AND_MOTION_V1.md"
COMPONENTS = ROOT / "apps/product/experience_shell/src/components.ts"
ACCOUNT = ROOT / "apps/product/experience_shell/src/account_components.ts"


def test_abu_persona_is_visible_without_replacing_standard_product_language() -> None:
    components = COMPONENTS.read_text(encoding="utf-8")
    account = ACCOUNT.read_text(encoding="utf-8")

    assert "阿布同步论命" in components
    assert "命理档案" in account
    assert "登录" in account
    assert "汪！" not in components + account
    assert "缘分锦囊" not in components + account
    assert "流年密档" not in components + account


def test_abu_guidance_uses_journey_states_and_preserves_birth_time_uncertainty() -> None:
    account = ACCOUNT.read_text(encoding="utf-8")
    motion_registry = MOTION_REGISTRY.read_text(encoding="utf-8")

    for state in ("welcome", "listening", "parsing", "confirming", "thinking", "probe", "completed", "boundary"):
        assert f'{state}: "' in motion_registry

    assert 'name="time_precision"' in account
    assert 'value="approximate"' in account
    assert "修改出生资料会建立新的命盘版本" in account


def test_abu_contract_freezes_agent_and_action_boundaries() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "Abu is not a decorative mascot" in contract
    assert "Journey Runtime chooses the authorized next action" in contract
    assert "abu_creates_mingli_claim: false" in contract
    assert "birth_confirmation_required_before_compute: true" in contract
    assert "approximate_time_remains_approximate: true" in contract
