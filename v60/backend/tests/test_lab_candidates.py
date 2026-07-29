from abu_v60.context import build_experience_context
from abu_v60.knowledge import SOURCE_REF
from abu_v60.lab import LabProjector
from abu_v60.mingli import (
    CandidateQualificationEngine,
    CandidateQualificationStatus,
    StructuralCandidateCompiler,
)


def _relation_fact(**overrides: object) -> dict[str, object]:
    fact: dict[str, object] = {
        "fact_ref": "fact:harmony-month-hour",
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
        "source_ref": SOURCE_REF,
    }
    fact.update(overrides)
    return fact


def _context():
    return build_experience_context(
        actor_name="测试角色",
        cutoff_tick=0,
        current_tick=0,
        lineage={
            "encounter_ref": "encounter:test",
            "correlation_id": "correlation:test",
            "causation_id": "cause:test",
            "actor_ref": "actor:test",
            "tree_ref": "tree:test",
            "world_ref": "world:test",
            "case_ref": "case:test",
            "life_case_revision_ref": "life-case:test",
            "chart_version_ref": "chart:v1",
            "scene_ref": "scene:test",
            "question_ref": "question:test",
            "world_event_ref": "event:test",
        },
        progress={
            "observed_organs": [],
            "question_visible": False,
            "answer_sealed": False,
            "world_settled": False,
            "revealed": False,
            "reconciled": False,
        },
        narrative_scene_ref="theater:test",
        narrative_moment={
            "phase": "OBSERVING",
            "content_key": "test.story.observing",
            "title": "测试生命线",
            "status_line": "测试状态",
            "theater_beat": "测试已提交场景。",
            "abu_line": "先看已经发生的事。",
            "disclosure": "BASELINE_ONLY",
        },
        pillars={"year": "辛未", "month": "丙申", "day": "丙辰", "hour": "癸巳"},
        facts=(_relation_fact(),),
        baseline_evidence=(
            {
                "evidence_ref": "evidence:test",
                "summary": "测试基线。",
                "observed_at_tick": 0,
                "epistemic_role": "DECISION_BASELINE_NO_CREDIT",
            },
        ),
    )


def test_relation_fact_compiles_to_stable_unresolved_candidate() -> None:
    compiler = StructuralCandidateCompiler()
    first = compiler.compile(
        chart_version_ref="chart:v1",
        facts=(_relation_fact(),),
    )
    replay = compiler.compile(
        chart_version_ref="chart:v1",
        facts=(_relation_fact(),),
    )

    assert first == replay
    assert len(first) == 1
    candidate = first[0]
    assert candidate.label == "月支申与时支巳的六合结构候选"
    assert candidate.evidence_refs == ("fact:harmony-month-hour",)
    assert candidate.structure_evidence_status is CandidateQualificationStatus.SATISFIED
    assert len(candidate.qualification_receipts) == 1
    receipt = candidate.qualification_receipts[0]
    assert receipt.status is CandidateQualificationStatus.SATISFIED
    assert receipt.selection_authority is False
    assert receipt.evidence_refs == ("fact:harmony-month-hour",)
    assert "effective_work" in receipt.forbidden_conclusions
    assert receipt == replay[0].qualification_receipts[0]
    assert candidate.selection_qualified is False
    assert candidate.effect_status.value == "UNRESOLVED"
    assert candidate.capacity_status.value == "UNRESOLVED"
    assert candidate.professional_admission_status.value == "UNRESOLVED"


def test_non_relation_or_unbounded_fact_cannot_become_candidate() -> None:
    compiler = StructuralCandidateCompiler()
    candidates = compiler.compile(
        chart_version_ref="chart:v1",
        facts=(
            _relation_fact(fact_type="hidden_stem_membership"),
            _relation_fact(authority="MODEL_GENERATED"),
            _relation_fact(
                fact_json={
                    "left_branch": "申",
                    "right_branch": "巳",
                    "left_slot": "month",
                    "right_slot": "hour",
                    "membership_only": False,
                    "effect_not_inferred": True,
                }
            ),
        ),
    )

    assert candidates == ()


def test_qualification_rejects_source_drift_and_unadmitted_fact_type() -> None:
    candidate = StructuralCandidateCompiler().compile(
        chart_version_ref="chart:v1",
        facts=(_relation_fact(),),
    )[0]
    engine = CandidateQualificationEngine()

    source_drift = engine.evaluate_structure_evidence(
        candidate=candidate,
        fact=_relation_fact(source_ref="profile:unadmitted"),
    )
    assert source_drift.status is CandidateQualificationStatus.REJECTED
    assert source_drift.missing_claims == ("required_source_ref",)
    assert source_drift.selection_authority is False

    no_rule = engine.evaluate_structure_evidence(
        candidate=candidate,
        fact=_relation_fact(fact_type="hidden_stem_membership"),
    )
    assert no_rule.status is CandidateQualificationStatus.NOT_ADMITTED
    assert no_rule.rule_ref is None
    assert no_rule.selection_authority is False


def test_lab_projects_candidate_but_kernel_refuses_to_select_it() -> None:
    projection = LabProjector().project(context=_context())

    assert projection["candidate_projection_status"] == ("STRUCTURE_CANDIDATES_AVAILABLE")
    assert len(projection["candidate_paths"]) == 1
    assert projection["decision_route"]["status"] == "UNRESOLVED"
    assert projection["decision_route"]["authority"] == "NONE"
    assert projection["decision_route"]["selected_candidate_ref"] is None
    assert projection["qualification_summary"]["structure_evidence_satisfied"] == 1
    assert projection["qualification_summary"]["selection_qualified"] == 0
    assert projection["canonical_write_allowed"] is False
