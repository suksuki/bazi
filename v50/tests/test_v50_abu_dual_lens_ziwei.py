from __future__ import annotations

from core.contracts import BirthInputCanonical, CalendarType, Gender
from core.abu_runtime import AbuRuntimeContext, resolve_abu_command
from core.engines import resolve_birth_input_pillars
from core.engines.ziwei.iztro_bridge import calculate_iztro_plate
from core.mingli_agent.world import compile_chart_world
from core.mingli_agent.contracts import DiscriminatingProbe, DualLensCognitionDraft, ZiweiLensObservation
from core.mingli_agent.reasoner import _dual_lens_errors


def _birth(*, birth_time: str = "03:30", explicit_mismatch: bool = False) -> BirthInputCanonical:
    birth = BirthInputCanonical(
        birth_input_id=f"birth.dual.lens.{birth_time}",
        name="双镜头验证",
        gender=Gender.FEMALE,
        calendar_type=CalendarType.SOLAR,
        birth_date="2000-08-16",
        birth_time=birth_time,
        birth_location="Shanghai",
        timezone="Asia/Shanghai",
    )
    if explicit_mismatch:
        return birth.model_copy(update={
            "year_pillar": "甲子",
            "month_pillar": "丙寅",
            "day_pillar": "丙寅",
            "hour_pillar": "庚寅",
            "input_quality": "explicit_pillars",
        })
    return resolve_birth_input_pillars(birth)


def test_iztro_bridge_matches_official_quick_start_example() -> None:
    plate = calculate_iztro_plate(birth_input=_birth(), analysis_year=2026)

    assert plate["source"] == "iztro@2.5.8"
    assert plate["soul_palace_branch"] == "午"
    assert plate["body_palace_branch"] == "戌"
    assert plate["soul_star"] == "破军"
    assert plate["body_star"] == "文昌"
    assert plate["five_elements_class"] == "木三局"
    assert plate["reasoning_ready"] is True
    assert len(plate["palaces"]) == 12


def test_changed_birth_hour_changes_ziwei_stage_without_mutating_birth_facts() -> None:
    first = _birth(birth_time="03:30")
    second = _birth(birth_time="15:30")
    first_plate = calculate_iztro_plate(birth_input=first, analysis_year=2026)
    second_plate = calculate_iztro_plate(birth_input=second, analysis_year=2026)

    assert first.birth_date == second.birth_date == "2000-08-16"
    assert first_plate["body_palace_branch"] != second_plate["body_palace_branch"]
    assert first_plate["time"] != second_plate["time"]


def test_explicit_bazi_pillar_mismatch_blocks_ziwei_reasoning() -> None:
    world = compile_chart_world(reading_id="reading.dual.blocked", birth_input=_birth(explicit_mismatch=True))

    assert world.ziwei_profile["status"] == "blocked"
    assert world.ziwei_profile["reasoning_ready"] is False
    assert "ziwei_bazi_pillar_mismatch" in world.ziwei_profile["warnings"]
    assert [fact.category for fact in world.facts if fact.category.startswith("ziwei_")] == ["ziwei_source_quality"]


def test_month_pillar_convention_difference_is_visible_but_not_falsely_blocked() -> None:
    birth = BirthInputCanonical(
        birth_input_id="birth.month.convention",
        name="月柱口径验证",
        gender=Gender.MALE,
        calendar_type=CalendarType.SOLAR,
        birth_date="1988-05-12",
        birth_time="09:30",
        birth_location="Shanghai",
        timezone="Asia/Shanghai",
        year_pillar="戊辰",
        month_pillar="丁巳",
        day_pillar="丁卯",
        hour_pillar="乙巳",
        input_quality="calendar_derived_pillars",
    )
    plate = calculate_iztro_plate(birth_input=birth, analysis_year=2026)

    assert plate["pillar_differences"] == ["month"]
    assert plate["reasoning_ready"] is True
    assert "ziwei_bazi_month_pillar_convention_difference" in plate["warnings"]


def test_aligned_birth_exposes_bounded_ziwei_world_facts() -> None:
    world = compile_chart_world(reading_id="reading.dual.ready", birth_input=_birth())
    categories = {fact.category for fact in world.facts}

    assert world.ziwei_profile["status"] == "ready"
    assert world.ziwei_profile["calculator"] == "iztro@2.5.8"
    assert {"ziwei_palace", "ziwei_star", "ziwei_four_transformation", "ziwei_time_window"}.issubset(categories)
    assert any(ref.startswith("ziwei.") for ref in world.allowed_evidence_refs)


def test_abu_can_navigate_dual_lenses_without_creating_judgment() -> None:
    ready = resolve_abu_command(message="我想看看紫微怎么说", context=AbuRuntimeContext(has_case=True))
    missing = resolve_abu_command(message="先看八字", context=AbuRuntimeContext(has_case=False))

    assert ready.capability_id == "reading.select_lens"
    assert ready.slots == {"lens": "ziwei"}
    assert ready.executor == "client_ui"
    assert ready.missing_requirements == []
    assert missing.slots == {"lens": "bazi"}
    assert missing.missing_requirements == ["confirmed_chart"]


def test_abu_routes_non_reasoning_actions_and_domain_resume_without_core_llm() -> None:
    context = AbuRuntimeContext(has_case=True, active_mode="member")

    language = resolve_abu_command(message="切换到英文", context=context)
    month = resolve_abu_command(message="看看上个月", context=context)
    reality = resolve_abu_command(message="记录昨天发生的一件事情", context=context)
    career = resolve_abu_command(message="继续刚才的事业讨论", context=context)

    assert language.capability_id == "interface.language"
    assert language.executor == "client_ui"
    assert month.capability_id == "timeline.select_period"
    assert month.executor == "client_ui"
    assert reality.capability_id == "reality.record"
    assert reality.executor == "client_ui"
    assert career.capability_id == "reading.select_domain"
    assert career.slots == {"domain": "career"}


def test_dual_lens_guard_allows_explicit_denial_of_deterministic_events() -> None:
    world = compile_chart_world(reading_id="reading.dual.guard", birth_input=_birth())
    draft = DualLensCognitionDraft(
        ziwei_first_look="命宫与事业舞台形成可观察的角色倾向。",
        identity_axis="内在结构与外在角色需要一起验证。",
        palace_observations=[
            ZiweiLensObservation(observation_id="z1", domain="identity", claim="更重视自主判断。", why_it_matters="关系到角色选择。", evidence_refs=["ziwei.palace.identity"]),
            ZiweiLensObservation(observation_id="z2", domain="career", claim="事业需要承担复杂任务。", why_it_matters="关系到能力兑现。", evidence_refs=["ziwei.topic_palace_names"]),
        ],
        agreements=["两种视角都指向自主判断。"],
        tensions=[],
        integrated_thesis="长期结构需要在具体角色中兑现。",
        current_stage_note="当前舞台被激活，但并不代表必然发生某个事件。",
        cross_lens_probe=DiscriminatingProbe(probe_id="zp", question="面对复杂任务时你会先整理方法，还是先确认角色边界？", purpose="区分长期倾向和当前角色。", distinguishes_hypothesis_refs=["h1", "ziwei-stage"], options=["先整理方法", "先确认边界"], expected_updates={"先整理方法": "增强h1", "先确认边界": "增强ziwei-stage"}),
        uncertainties=["仍需现实行为验证"],
        evidence_refs=["ziwei.palace.identity"],
    )

    assert "紫微时序不得写成确定事件" not in _dual_lens_errors(dual_lens=draft, world=world)
