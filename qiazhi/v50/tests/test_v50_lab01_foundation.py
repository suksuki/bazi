from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.graph import (
    AssertionLifecycle,
    PathAssertion,
    ProvenanceRecord,
    RelationAssertion,
)
from experience.canonical_scene import (
    compile_canonical_projection,
    compile_canonical_scene,
)
from experience.lab import (
    LabCandidateRevision,
    LabEvidenceSet,
    LabPathComparison,
    append_lab_candidate_revision,
    build_lab_promotion_proposal,
    issue_lab_session,
    open_lab_study,
    record_lab_path_comparison,
    update_lab_evidence,
)
from product.canonical_scene import canonical_scene_source_from_case_row
from test_v50_mingli_structural_experiment import _case_payload


NOW = datetime(2026, 7, 21, 8, 0, tzinfo=timezone.utc)


def _source_scene_projection(*, role: str = "research"):
    case_id = "case-lab01-foundation"
    payload = _case_payload(case_id)
    source = canonical_scene_source_from_case_row(case_id=case_id, row=payload)
    scene = compile_canonical_scene(source=source, role=role)
    projection = compile_canonical_projection(scene=scene, kind="workspace")
    return source, scene, projection


def _study(*, source_mode: str = "canonical_projection"):
    source, _, projection = _source_scene_projection()
    session = issue_lab_session(
        projection=projection,
        session_id="lab-session-01",
        participant_run_id="research-run-01",
        experiment_kind=(
            "synthetic_case" if source_mode == "synthetic_fixture" else "relation_inspection"
        ),
        base_snapshot_ref="snapshot-lab01",
        source_mode=source_mode,
        synthetic_fixture_ref=(
            "fixture:synthetic:lab01" if source_mode == "synthetic_fixture" else ""
        ),
        now=NOW,
    )
    study = open_lab_study(
        session=session,
        projection=projection,
        source=source,
        study_id="study-lab01",
        now=NOW,
    )
    return source, projection, study


def _candidate_revision(study, *, revision: int = 1) -> LabCandidateRevision:
    provenance = ProvenanceRecord(
        source="graph_candidate",
        producer_id="mingli-lab",
        producer_version=f"lab01-candidate-v{revision}",
        evidence_refs=[f"fixture:lab01:{revision}"],
        source_refs=[study.scene_identity.source_hash],
        created_at=f"2026-07-21T08:0{revision}:00+00:00",
    )
    formal_relation = study.formal_relation_assertions[0]
    formal_path = next(
        item for item in study.formal_path_assertions if item.path_key is not None
    )
    relation = RelationAssertion(
        relation_key=formal_relation.relation_key,
        assertion_version=f"lab01:candidate:{revision}",
        status=AssertionLifecycle.CANDIDATE,
        provenance=provenance,
        statement="研究候选关系，不写回正式案例。",
    )
    path = PathAssertion(
        path_key=formal_path.path_key,
        assertion_version=f"lab01:candidate:{revision}",
        status=AssertionLifecycle.CANDIDATE,
        provenance=provenance,
        statement="研究候选路径，不覆盖正式路径。",
    )
    return LabCandidateRevision(
        revision_id=f"candidate-revision-{revision}",
        revision=revision,
        relation_assertions=[relation],
        path_assertions=[path],
        interpretation="用于对比正式认知与候选解释。",
        conditions=["正样本、负样本和边界样本均通过"],
        counter_signals=["反例仍未解释"],
        supersedes_revision_id=(
            f"candidate-revision-{revision - 1}" if revision > 1 else ""
        ),
        created_at=NOW.replace(minute=revision),
    )


def test_lab01_reuses_canonical_scene_and_disclosed_formal_assertions() -> None:
    source, projection, study = _study()

    assert study.scene_identity == projection.scene_identity
    assert study.session.scene_source_hash == projection.scene_identity.source_hash
    assert study.disclosed_relation_assertion_refs == (
        projection.role_disclosure.visible_relation_assertion_refs
    )
    assert study.disclosed_path_assertion_refs == (
        projection.role_disclosure.visible_path_assertion_refs
    )
    assert [item.assertion_id for item in study.formal_relation_assertions] == (
        study.disclosed_relation_assertion_refs
    )
    assert [item.assertion_id for item in study.formal_path_assertions] == (
        study.disclosed_path_assertion_refs
    )
    assert {item.provenance_id for item in study.provenance_records} == {
        item.provenance.provenance_id
        for item in [*source.relation_assertions, *source.path_assertions]
    }
    assert study.writes_chart is False
    assert study.writes_life_case is False
    assert study.promotes_candidate is False


def test_lab01_candidate_revision_and_path_comparison_remain_isolated() -> None:
    source, _, study = _study()
    source_before = source.model_dump(mode="json")
    revision = _candidate_revision(study)
    revised = append_lab_candidate_revision(study, revision=revision)
    formal_path_ref = revised.formal_path_assertions[0].assertion_id
    candidate_path_ref = revision.path_assertions[0].assertion_id
    compared = record_lab_path_comparison(
        revised,
        comparison=LabPathComparison(
            comparison_id="comparison-lab01",
            path_assertion_refs=[formal_path_ref, candidate_path_ref],
            status="needs_evidence",
            reason_refs=["fixture:comparison:lab01"],
            created_at=NOW.replace(minute=2),
        ),
    )

    assert source.model_dump(mode="json") == source_before
    assert compared.formal_path_assertions == study.formal_path_assertions
    assert compared.candidate_revisions[0].writes_life_case is False
    assert compared.candidate_revisions[0].commits_assertion is False
    assert compared.path_comparisons[0].path_assertion_refs == [
        formal_path_ref,
        candidate_path_ref,
    ]
    assert all(
        item.status == AssertionLifecycle.CANDIDATE
        for item in [
            *revision.relation_assertions,
            *revision.path_assertions,
        ]
    )


def test_lab01_evidence_can_only_prepare_a_separate_risk_gate() -> None:
    _, _, study = _study()
    revision = _candidate_revision(study)
    study = append_lab_candidate_revision(study, revision=revision)

    blocked = build_lab_promotion_proposal(
        study,
        candidate_revision_id=revision.revision_id,
    )
    assert blocked.status == "blocked"
    assert set(blocked.missing_requirements) == {
        "positive_fixture",
        "negative_fixture",
        "boundary_fixture",
        "synthetic_case",
        "counterexample",
        "counterexamples_resolved",
        "regression",
    }

    study = update_lab_evidence(
        study,
        evidence=LabEvidenceSet(
            positive_fixture_refs=["fixture:positive:1"],
            negative_fixture_refs=["fixture:negative:1"],
            boundary_fixture_refs=["fixture:boundary:1"],
            synthetic_case_refs=["synthetic:case:1"],
            counterexample_refs=["counterexample:1"],
            resolved_counterexample_refs=["counterexample:1"],
            regression_refs=["regression:1"],
        ),
        now=NOW.replace(minute=3),
    )
    ready = build_lab_promotion_proposal(
        study,
        candidate_revision_id=revision.revision_id,
    )

    assert ready.status == "ready_for_risk_gate"
    assert ready.missing_requirements == []
    assert ready.requires_risk_gate is True
    assert ready.performs_promotion is False
    assert ready.writes_life_case is False


def test_lab01_requires_research_disclosure_and_never_recovers_hidden_assertions() -> None:
    source, _, member_projection = _source_scene_projection(role="member")
    session = issue_lab_session(
        projection=member_projection,
        session_id="member-lab-session",
        participant_run_id="member-run",
        experiment_kind="relation_inspection",
        base_snapshot_ref="snapshot-member",
        now=NOW,
    )

    with pytest.raises(ValueError, match="lab_study_requires_research_disclosure"):
        open_lab_study(
            session=session,
            projection=member_projection,
            source=source,
            study_id="member-study",
            now=NOW,
        )


def test_lab01_synthetic_case_still_requires_canonical_scene_and_fixture_ref() -> None:
    source, _, projection = _source_scene_projection()
    with pytest.raises(ValueError, match="synthetic_lab_session_requires_fixture_ref"):
        issue_lab_session(
            projection=projection,
            session_id="synthetic-without-fixture",
            participant_run_id="research-run",
            experiment_kind="synthetic_case",
            base_snapshot_ref="snapshot-synthetic",
            source_mode="synthetic_fixture",
            now=NOW,
        )

    synthetic_source, _, study = _study(source_mode="synthetic_fixture")
    assert study.session.synthetic_fixture_ref == "fixture:synthetic:lab01"
    assert study.session.scene_source_hash == study.scene_identity.source_hash
    assert study.scene_identity.life_case_id == synthetic_source.life_case_id
    assert study.scene_identity.case_ref == source.case_ref


def test_lab01_rejects_comparison_refs_outside_formal_and_candidate_views() -> None:
    _, _, study = _study()
    with pytest.raises(ValueError, match="lab_path_comparison_uses_unknown_assertion"):
        record_lab_path_comparison(
            study,
            comparison=LabPathComparison(
                comparison_id="unknown-comparison",
                path_assertion_refs=[
                    study.formal_path_assertions[0].assertion_id,
                    "hidden:path-assertion",
                ],
                created_at=NOW,
            ),
        )
