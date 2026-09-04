from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.experience.home import HomeExperienceService
from abu_v60.mingli import (
    MECHANISM_QUALIFICATION_DIMENSIONS,
    MingliMechanismEvidenceVector,
    MingliMechanismQualificationProjector,
    MingliQuantFoundationVector,
    MingliReadingEnvelope,
    MingliTimingEvidenceVector,
)
from abu_v60.provenance import canonical_json
from sqlalchemy import text


def _qualified_owner_accounts() -> tuple[str, ...]:
    with engine.connect() as connection:
        return tuple(
            str(item)
            for item in connection.execute(
                text(
                    """
                    SELECT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    GROUP BY owner_account_ref
                    HAVING count(*) = 1
                    ORDER BY owner_account_ref
                    """
                )
            ).scalars()
        )


def test_qualification_is_stable_and_bounded_across_active_owner_accounts() -> None:
    accounts = _qualified_owner_accounts()
    assert accounts

    refs: set[str] = set()
    for account_ref in accounts:
        service = HomeExperienceService(engine)
        first = service.snapshot(account_ref=account_ref)
        second = service.snapshot(account_ref=account_ref)
        qualification = first["mingli"]["mechanism_qualification"]

        assert qualification == second["mingli"]["mechanism_qualification"]
        assert qualification["reading_ref"] == first["mingli"]["reading"]["reading_ref"]
        assert (
            qualification["mechanism_vector_ref"]
            == (first["mingli"]["mechanism_evidence"]["vector_ref"])
        )
        assert (
            qualification["timing_vector_ref"] == (first["mingli"]["timing_evidence"]["vector_ref"])
        )
        assert first["lab"]["mechanism_qualification_ref"] == (qualification["qualification_ref"])
        assert (
            first["mingli"]["abu_expression"]["qualification_ref"]
            == (qualification["qualification_ref"])
        )
        assert qualification["professional_verdict_allowed"] is False
        assert qualification["probability_claim_allowed"] is False
        assert qualification["canonical_write_allowed"] is False
        assert qualification["read_only"] is True

        refs.add(str(qualification["qualification_ref"]))
        for candidate in qualification["candidates"]:
            assert [item["dimension"] for item in candidate["checks"]] == list(
                MECHANISM_QUALIFICATION_DIMENSIONS
            )
            checks = {item["dimension"]: item for item in candidate["checks"]}
            assert checks["STRUCTURAL_ROLES"]["status"] == "PRESENT"
            assert checks["STRUCTURAL_ROLES"]["evidence_refs"]
            assert checks["SOURCE_MANIFESTATION"]["status"] in {"PARTIAL", "MISSING"}
            assert checks["TIMING_OVERLAP"]["status"] in {"PARTIAL", "MISSING"}
            for dimension in (
                "COUNTER_EVIDENCE",
                "EFFECT",
                "CAPACITY",
                "USABILITY",
                "PROFESSIONAL_ADMISSION",
            ):
                assert checks[dimension]["status"] == "NOT_ADMITTED"
            assert all(item["next_evidence"] for item in candidate["checks"])
            assert all(item["falsifier"] for item in candidate["checks"])
            assert candidate["professional_admission"] is False
            assert candidate["readiness"] == "STRUCTURE_CANDIDATE_ONLY"

    assert len(refs) == len(accounts)


def test_qualification_contains_no_effective_work_or_probability_claim() -> None:
    snapshot = HomeExperienceService(engine).snapshot(account_ref=_qualified_owner_accounts()[0])
    serialized = canonical_json(snapshot["mingli"]["mechanism_qualification"])

    assert '"professional_verdict_allowed":false' in serialized
    assert '"probability_claim_allowed":false' in serialized
    assert '"professional_admission":false' in serialized
    assert "PROFESSIONALLY_ADMITTED" not in serialized
    assert "EFFECTIVE_WORK" not in serialized
    assert "support_score" not in serialized


def test_qualification_rejects_cross_case_lineage() -> None:
    snapshot = HomeExperienceService(engine).snapshot(account_ref=_qualified_owner_accounts()[0])
    mingli = snapshot["mingli"]
    reading = MingliReadingEnvelope.model_validate(mingli["reading"])
    quant = MingliQuantFoundationVector.model_validate(mingli["quant_foundation"])
    mechanism = MingliMechanismEvidenceVector.model_validate(mingli["mechanism_evidence"])
    timing = MingliTimingEvidenceVector.model_validate(mingli["timing_evidence"])

    with pytest.raises(
        ValueError,
        match="mechanism_qualification_case_lineage_mismatch",
    ):
        MingliMechanismQualificationProjector().project(
            reading=reading,
            quant_vector=quant.model_copy(update={"case_ref": "case:other"}),
            mechanism_vector=mechanism,
            timing_vector=timing,
        )
