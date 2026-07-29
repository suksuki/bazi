from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.experience.home import HomeExperienceService
from abu_v60.mingli import (
    MECHANISM_EVIDENCE_CHANNEL_ORDER,
    MECHANISM_UNRESOLVED_DIMENSIONS,
    MingliMechanismEvidenceDepthProjector,
    MingliMechanismEvidenceVector,
    MingliQuantFoundationVector,
    MingliReadingEnvelope,
    MingliTimingEvidenceVector,
)
from abu_v60.provenance import canonical_json
from sqlalchemy import text


def _corpus_vectors() -> list[dict[str, object]]:
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT ON (reading.case_ref)
                           reading.case_ref,
                           reading.reading_json,
                           quant.vector_json AS quant_json,
                           mechanism.vector_json AS mechanism_json,
                           timing.vector_json AS timing_json
                    FROM mingli.readings AS reading
                    JOIN mingli.cases AS life_case
                      ON life_case.case_ref = reading.case_ref
                    JOIN mingli.quant_foundation_vectors AS quant
                      ON quant.vector_ref = reading.quant_vector_ref
                    JOIN mingli.mechanism_evidence_vectors AS mechanism
                      ON mechanism.vector_ref = reading.mechanism_vector_ref
                    JOIN mingli.timing_evidence_vectors AS timing
                      ON timing.vector_ref = reading.timing_vector_ref
                    WHERE life_case.status = 'ACTIVE'
                      AND life_case.subject_kind IN ('HUMAN_OWNER', 'HUMAN_REFERENCE')
                    ORDER BY reading.case_ref, reading.created_at DESC
                    """
                )
            )
            .mappings()
            .all()
        )
    return [dict(item) for item in rows]


def _owner_account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    GROUP BY owner_account_ref
                    HAVING count(*) = 1
                    ORDER BY owner_account_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )


def test_depth_projection_is_stable_and_bounded_across_private_corpus() -> None:
    rows = _corpus_vectors()
    assert len(rows) >= 20
    projector = MingliMechanismEvidenceDepthProjector()
    depth_refs: set[str] = set()
    candidate_count = 0

    for row in rows:
        reading = MingliReadingEnvelope.model_validate(row["reading_json"])
        quant = MingliQuantFoundationVector.model_validate(row["quant_json"])
        mechanism = MingliMechanismEvidenceVector.model_validate(row["mechanism_json"])
        timing = MingliTimingEvidenceVector.model_validate(row["timing_json"])
        first = projector.project(
            reading=reading,
            quant_vector=quant,
            mechanism_vector=mechanism,
            timing_vector=timing,
            mechanism_comparison={"selected_candidate_ref": None},
        )
        second = projector.project(
            reading=reading,
            quant_vector=quant,
            mechanism_vector=mechanism,
            timing_vector=timing,
            mechanism_comparison={"selected_candidate_ref": None},
        )

        assert first == second
        assert first.case_ref == row["case_ref"]
        assert first.professional_verdict_allowed is False
        assert first.probability_claim_allowed is False
        assert first.canonical_write_allowed is False
        assert first.read_only is True
        depth_refs.add(first.depth_ref)
        candidate_count += len(first.candidates)

        for candidate in first.candidates:
            assert candidate.attention_status == "UNRANKED"
            assert candidate.evidence_channels == tuple(
                item
                for item in MECHANISM_EVIDENCE_CHANNEL_ORDER
                if item in candidate.evidence_channels
            )
            assert candidate.unresolved_dimensions == (MECHANISM_UNRESOLVED_DIMENSIONS)
            assert candidate.evidence_score_status == "NOT_COMPUTED"
            assert candidate.professional_admission is False
            assert all(role.direct_evidence_refs for role in candidate.roles)
            assert all(item.effect_status == "UNRESOLVED" for item in candidate.timing_relations)

    assert len(depth_refs) == len(rows)
    assert candidate_count >= len(rows)


def test_home_depth_uses_only_recorded_attention_selection() -> None:
    snapshot = HomeExperienceService(engine).snapshot(account_ref=_owner_account_ref())
    depth = snapshot["mingli"]["mechanism_evidence_depth"]
    selected_ref = snapshot["lab"]["mechanism_comparison"]["selected_candidate_ref"]

    assert snapshot["lab"]["mechanism_evidence_depth_ref"] == depth["depth_ref"]
    assert snapshot["lab"]["mechanism_evidence_depth_hash"] == depth["depth_hash"]
    assert snapshot["lab"]["mechanism_evidence_depth_candidates"] == depth["candidates"]
    primary = [
        item for item in depth["candidates"] if item["attention_status"] == "PRIMARY_ATTENTION"
    ]
    assert [item["candidate_ref"] for item in primary] == (
        [selected_ref] if selected_ref is not None else []
    )
    if primary:
        direct_refs = set(
            next(
                item
                for item in snapshot["lab"]["mechanism_candidates"]
                if item["candidate_ref"] == selected_ref
            )["competing_candidate_refs"]
        )
        assert {
            item["candidate_ref"]
            for item in depth["candidates"]
            if item["attention_status"] == "DIRECT_COMPETITOR"
        } == direct_refs

    serialized = canonical_json(depth)
    assert '"evidence_score_status":"NOT_COMPUTED"' in serialized
    assert '"professional_verdict_allowed":false' in serialized
    assert '"probability_claim_allowed":false' in serialized
    assert "EFFECTIVE_WORK" not in serialized
    assert "support_score" not in serialized


def test_depth_projection_rejects_invalid_selection_and_cross_case_lineage() -> None:
    row = _corpus_vectors()[0]
    reading = MingliReadingEnvelope.model_validate(row["reading_json"])
    quant = MingliQuantFoundationVector.model_validate(row["quant_json"])
    mechanism = MingliMechanismEvidenceVector.model_validate(row["mechanism_json"])
    timing = MingliTimingEvidenceVector.model_validate(row["timing_json"])
    projector = MingliMechanismEvidenceDepthProjector()

    with pytest.raises(
        ValueError,
        match="mechanism_depth_selected_candidate_not_in_vector",
    ):
        projector.project(
            reading=reading,
            quant_vector=quant,
            mechanism_vector=mechanism,
            timing_vector=timing,
            mechanism_comparison={"selected_candidate_ref": "candidate:unknown"},
        )

    with pytest.raises(ValueError, match="mechanism_depth_case_lineage_mismatch"):
        projector.project(
            reading=reading,
            quant_vector=quant.model_copy(update={"case_ref": "case:other"}),
            mechanism_vector=mechanism,
            timing_vector=timing,
            mechanism_comparison={"selected_candidate_ref": None},
        )
