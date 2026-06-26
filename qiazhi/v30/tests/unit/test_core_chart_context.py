from __future__ import annotations

from datetime import datetime, timezone

from v30.core.chart_context import build_chart_context_from_displays


def test_build_chart_context_from_explicit_pillars() -> None:
    context = build_chart_context_from_displays(
        reading_id="core-test",
        year="甲子",
        month="乙丑",
        day="丙寅",
        hour="丁卯",
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    assert context.context_id.startswith("v30.bazi_context.")
    assert context.day_master == "丙"
    assert context.day_master_element == "fire"
    assert context.natal_pillars["pillars"]["day"]["stem"] == "丙"
    assert context.input_pillars["source"] == "explicit_pillars"
    assert context.input_pillars["chart_build_source"]["status"] == "ready"
    assert context.input_pillars["chart_build_source"]["calendar_assumption"] == "explicit_pillars_no_calendar_conversion"
    summary = context.natal_pillars["base_fact_summary"]
    assert summary["version"] == "v30.base_bazi_fact_summary.v1"
    assert summary["status"] == "ready"
    assert summary["pillar_count"] == 4
    assert summary["visible_ten_god_count"] == 3
    assert summary["hidden_ten_god_count"] > 0
    assert summary["visible_ten_god_counts"]
    assert summary["hidden_ten_god_counts"]
    assert summary["hidden_stem_summary"]
    assert "relation_type_counts" in summary
    assert "relation_families" in summary
    root_summary = summary["root_fact_summary"]
    assert root_summary["version"] == "v30.root_vault_fact_summary.v1"
    assert root_summary["status"] == "ready"
    assert root_summary["same_element_root_count"] >= root_summary["day_master_root_count"]
    assert root_summary["boundary"] == "root_vault_summary_records_presence_without_strength_or_useful_god_verdict"
    assert "NO_STRENGTH_VERDICT_FROM_ROOT_FACTS" in root_summary["guardrails"]
    assert summary["element_distribution"]
    assert summary["boundary"] == "base_bazi_fact_summary_expands_chart_facts_without_judgment"
    assert "NO_STRENGTH_OR_USEFUL_GOD_VERDICT" in summary["guardrails"]
    assert context.time_layers["status"] == "not_provided"
    assert context.natal_pillars["visible_ten_gods"]
    assert context.natal_pillars["hidden_ten_gods"]


def test_build_chart_context_with_time_layers() -> None:
    context = build_chart_context_from_displays(
        reading_id="core-time-test",
        year="甲子",
        month="乙丑",
        day="丙寅",
        hour="丁卯",
        luck_pillar="庚午",
        flow_year_pillar="辛未",
    )
    assert context.time_layers["status"] == "ready"
    assert [row["layer_key"] for row in context.time_layers["layers"]] == ["luck", "flow_year"]
