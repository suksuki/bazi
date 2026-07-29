from __future__ import annotations

import pytest
from abu_v60.context import ExperienceUnit, build_experience_context
from abu_v60.experience import ExperienceProjectionComposer
from abu_v60.provenance import canonical_json
from pydantic import ValidationError


def _fact(ref: str = "fact:harmony") -> dict[str, object]:
    return {
        "fact_ref": ref,
        "fact_type": "six_harmony_membership",
        "subject_ref": "pillar:month:branch:申",
        "object_ref": "pillar:hour:branch:巳",
        "authority": "SYSTEM_DETERMINISTIC_BOUNDED",
        "fact_json": {
            "left_branch": "申",
            "right_branch": "巳",
            "left_slot": "month",
            "right_slot": "hour",
            "membership_only": True,
            "effect_not_inferred": True,
        },
        "source_ref": "foundation-profile:v1",
    }


def _evidence(ref: str = "evidence:grass", tick: int = 12) -> dict[str, object]:
    return {
        "evidence_ref": ref,
        "summary": "引水草已经放回旧水渠，长期效果尚未确定。",
        "observed_at_tick": tick,
        "epistemic_role": "DECISION_BASELINE_NO_CREDIT",
    }


def _revealed_evidence(
    ref: str = "evidence:water-reached-roots",
    tick: int = 14,
) -> dict[str, object]:
    return {
        "evidence_ref": ref,
        "summary": "后续水流已经抵达坡下根系。",
        "committed_at_tick": tick,
        "epistemic_role": "OUTCOME_EVIDENCE",
    }


def _context(
    *,
    progress: dict[str, object] | None = None,
    facts: tuple[dict[str, object], ...] | None = None,
    evidence: tuple[dict[str, object], ...] | None = None,
    revealed_evidence: tuple[dict[str, object], ...] = (),
    decision_refs: tuple[str, ...] = (),
):
    resolved_progress = progress or {
        "observed_organs": ["leaf:1"],
        "question_visible": True,
        "answer_sealed": False,
        "world_settled": False,
        "revealed": False,
        "reconciled": False,
    }
    phase, disclosure = (
        ("COMPLETED", "OUTCOME_REVEALED")
        if resolved_progress["reconciled"]
        else ("REVEALED", "OUTCOME_REVEALED")
        if resolved_progress["revealed"]
        else ("REVEAL_READY", "WORLD_COMMITTED_HIDDEN")
        if resolved_progress["world_settled"]
        else ("WAITING_FOR_WORLD", "SEALED_NO_OUTCOME")
        if resolved_progress["answer_sealed"]
        else ("QUESTION_OPEN", "BASELINE_ONLY")
        if resolved_progress["question_visible"]
        else ("OBSERVING", "BASELINE_ONLY")
    )
    return build_experience_context(
        actor_name="砚舟",
        cutoff_tick=12,
        current_tick=14,
        lineage={
            "encounter_ref": "encounter:1",
            "correlation_id": "correlation:1",
            "causation_id": "cause:1",
            "actor_ref": "actor:1",
            "tree_ref": "tree:1",
            "world_ref": "world:1",
            "case_ref": "case:1",
            "life_case_revision_ref": "life-case:1",
            "chart_version_ref": "chart:1",
            "scene_ref": "scene:1",
            "question_ref": "question:1",
            "world_event_ref": "world-event:1",
        },
        progress=resolved_progress,
        narrative_scene_ref="theater:1",
        narrative_moment={
            "phase": phase,
            "content_key": f"test.story.{phase.lower()}",
            "title": "测试生命线",
            "status_line": "测试状态",
            "theater_beat": "砚舟把引水草重新压进旧水渠石缝。",
            "abu_line": "先看已经发生的事。",
            "disclosure": disclosure,
        },
        pillars={"year": "辛未", "month": "丙申", "day": "丙辰", "hour": "癸巳"},
        facts=facts or (_fact(),),
        baseline_evidence=evidence or (_evidence(),),
        revealed_evidence=revealed_evidence,
        decision_refs=decision_refs,
    )


def test_context_is_stable_and_shared_by_all_product_units() -> None:
    context = _context(
        facts=(_fact("fact:z"), _fact("fact:a")),
        evidence=(_evidence("evidence:z"), _evidence("evidence:a")),
    )
    replay = _context(
        facts=(_fact("fact:a"), _fact("fact:z")),
        evidence=(_evidence("evidence:a"), _evidence("evidence:z")),
    )
    projections = ExperienceProjectionComposer().compose(context=context)

    assert context.context_ref == replay.context_ref
    assert context.context_hash == replay.context_hash
    assert {item["context_ref"] for item in projections.values()} == {context.context_ref}
    assert set(context.public_manifest()["unit_disclosures"]) == {
        unit.value for unit in ExperienceUnit
    }


def test_context_contains_no_hidden_choice_or_sealed_outcome() -> None:
    context = _context()
    serialized = canonical_json(context.model_dump(mode="json"))
    manifest = context.public_manifest()

    assert "npc_choice_id" not in serialized
    assert "sealed_outcome" not in serialized
    assert "resolved_proposition" not in serialized
    assert manifest["sealed_outcome_included"] is False
    assert manifest["hidden_npc_choice_included"] is False


def test_context_rejects_post_cutoff_or_outcome_evidence() -> None:
    with pytest.raises(
        ValidationError,
        match="post_cutoff_evidence_not_allowed_in_experience_context",
    ):
        _context(evidence=(_evidence(tick=13),))

    leaked = {
        **_evidence(),
        "atom": {"root_support": "stable"},
    }
    with pytest.raises(ValidationError, match="extra_forbidden"):
        _context(evidence=(leaked,))


def test_context_rejects_decision_refs_before_reveal() -> None:
    with pytest.raises(ValidationError, match="decision_refs_require_revealed_state"):
        _context(decision_refs=("decision:future",))

    context = _context(
        progress={
            "observed_organs": ["leaf:1", "leaf:2", "branch:1"],
            "question_visible": True,
            "answer_sealed": True,
            "world_settled": True,
            "revealed": True,
            "reconciled": False,
        },
        decision_refs=("decision:committed",),
    )
    theater = context.disclosure_for(ExperienceUnit.THEATER)

    assert "decision:committed" in theater.source_refs
    assert "DECISION" in [kind.value for kind in theater.source_kinds]


def test_revealed_evidence_is_phase_gated_and_theater_replaces_baseline() -> None:
    with pytest.raises(
        ValidationError,
        match="revealed_evidence_requires_revealed_state",
    ):
        _context(revealed_evidence=(_revealed_evidence(),))

    revealed_progress = {
        "observed_organs": ["leaf:1", "leaf:2", "branch:1"],
        "question_visible": True,
        "answer_sealed": True,
        "world_settled": True,
        "revealed": True,
        "reconciled": False,
    }
    context = _context(
        progress=revealed_progress,
        revealed_evidence=(_revealed_evidence(),),
        decision_refs=("decision:committed",),
    )
    projections = ExperienceProjectionComposer().compose(context=context)
    theater = projections["theater"]

    assert theater["evidence_refs"] == ["evidence:water-reached-roots"]
    assert "evidence:grass" not in theater["evidence_refs"]
    assert context.public_manifest()["source_counts"]["revealed_evidence"] == 1


@pytest.mark.parametrize("tick", (12, 15))
def test_revealed_evidence_requires_valid_world_horizon(tick: int) -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "revealed_evidence_must_follow_question_cutoff"
            if tick == 12
            else "revealed_evidence_cannot_follow_current_tick"
        ),
    ):
        _context(
            progress={
                "observed_organs": ["leaf:1", "leaf:2", "branch:1"],
                "question_visible": True,
                "answer_sealed": True,
                "world_settled": True,
                "revealed": True,
                "reconciled": False,
            },
            revealed_evidence=(_revealed_evidence(tick=tick),),
            decision_refs=("decision:committed",),
        )


def test_abu_disclosure_cannot_read_evidence_or_mingli_facts() -> None:
    disclosure = _context().disclosure_for(ExperienceUnit.ABU)

    assert "evidence:grass" not in disclosure.source_refs
    assert "fact:harmony" not in disclosure.source_refs
    assert [kind.value for kind in disclosure.source_kinds] == [
        "ENCOUNTER",
        "ACTOR",
        "QUESTION",
        "SCENE",
    ]


def test_context_rejects_narrative_phase_or_disclosure_drift() -> None:
    base = {
        "phase": "WAITING_FOR_WORLD",
        "content_key": "test.story.waiting",
        "title": "等待",
        "status_line": "世界继续",
        "theater_beat": "判断已经封存。",
        "abu_line": "让世界走一段。",
        "disclosure": "SEALED_NO_OUTCOME",
    }
    context = _context(
        progress={
            "observed_organs": ["leaf:1"],
            "question_visible": True,
            "answer_sealed": False,
            "world_settled": False,
            "revealed": False,
            "reconciled": False,
        }
    )
    payload = context.model_dump(mode="json")
    payload["story"] = {"scene_ref": "theater:1", **base}

    with pytest.raises(
        ValidationError,
        match="experience_story_phase_progress_mismatch",
    ):
        type(context).model_validate(payload)
