from __future__ import annotations

from datetime import datetime, timezone

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input


def test_birth_input_with_gender_builds_luck_flow_and_six_pillar_context() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="luck-flow-ready",
        birth_input=BirthInput(
            input_id="luck-flow-input",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            gender="male",
        ),
        created_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
    )

    assert result.chart_context is not None
    layers = result.chart_context.time_layers
    assert layers["status"] == "ready"
    assert layers["luck_cycle_context"]["status"] == "ready"
    assert layers["luck_cycle_context"]["current_luck_pillar"]
    assert layers["flow_context"]["status"] == "ready"
    assert layers["flow_context"]["flow_year_pillar"]
    assert layers["six_pillar_context"]["status"] == "ready"
    assert len(layers["six_pillar_context"]["pillars"]) >= 6


def test_birth_input_without_gender_keeps_luck_pending_without_blocking_flow() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="luck-flow-gender-pending",
        birth_input=BirthInput(
            input_id="luck-flow-gender-pending-input",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
        ),
        created_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
    )

    assert result.chart_context is not None
    layers = result.chart_context.time_layers
    assert layers["luck_cycle_context"]["status"] == "pending"
    assert "gender_required_for_luck_direction" in layers["luck_cycle_context"]["missing_requirements"]
    assert layers["flow_context"]["status"] == "ready"
    assert layers["six_pillar_context"]["status"] == "pending"
