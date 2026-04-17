from __future__ import annotations

from app.prompts.final_verdict_user_locale import FinalVerdictUserLocale


def test_user_locale_zh_keeps_chinese_banners() -> None:
    loc = FinalVerdictUserLocale("ZH")
    assert "[ConfirmedDecisions · 用户意志]" in loc.banner_confirmed_decisions()
    assert "[User Will · persistence_layer · 终审最高权重]" in loc.banner_user_will()


def test_user_locale_en_localizes_confirmed_decisions_banner() -> None:
    loc = FinalVerdictUserLocale("EN")
    assert "[ConfirmedDecisions · user will]" in loc.banner_confirmed_decisions()
    assert "final_verdict_max_priority" in loc.banner_user_will()
    assert "VF tags" in loc.vf_narrative_rules(contract_polish=False)


def test_user_locale_ko_confirmed_decisions() -> None:
    loc = FinalVerdictUserLocale("KO")
    assert "사용자 의지" in loc.banner_confirmed_decisions()
