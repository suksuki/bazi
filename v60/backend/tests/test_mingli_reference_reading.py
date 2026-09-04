from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.mingli.reading_summary import MingliReadingSummaryService
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode
from sqlalchemy import text


def _reference_fixture() -> tuple[str, str]:
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref, case_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_REFERENCE'
                      AND status = 'ACTIVE'
                    ORDER BY owner_account_ref, created_at, case_ref
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .one()
        )
    return str(row["owner_account_ref"]), str(row["case_ref"])


def test_private_reference_is_listed_and_projects_its_own_formal_reading() -> None:
    account_ref, case_ref = _reference_fixture()
    service = MingliStageService(engine)
    subject_id = f"case:{case_ref}"

    subject = next(
        item
        for item in service.subjects(account_ref=account_ref)
        if item["subject_id"] == subject_id
    )
    stage = service.project(
        account_ref=account_ref,
        subject_id=subject_id,
        stage_mode=MingliStageMode.NATAL_4,
    )
    summary = MingliReadingSummaryService(engine).project(
        account_ref=account_ref,
        case_ref=case_ref,
    )

    assert subject["subject_kind"] == "HUMAN_REFERENCE"
    assert subject["identity_badge"] == "真实参考档案"
    assert stage.subject_kind == "HUMAN_REFERENCE"
    assert stage.privacy_scope == "PRIVATE_REFERENCE"
    assert stage.reading_ref is not None
    assert (
        summary.case_ref,
        summary.chart_version_ref,
        summary.life_case_revision_ref,
        summary.reading_ref,
        summary.reading_hash,
    ) == (
        stage.case_ref,
        stage.chart_version_ref,
        stage.life_case_revision_ref,
        stage.reading_ref,
        stage.reading_hash,
    )
    assert summary.reading_brief["qualification"]["status"] == ("FORMAL_BOUNDED_READING")
    assert summary.agent_status == "NOT_GENERATED"
    assert summary.agent_reading is None
    assert summary.claim_graph is None
    assert summary.agent_projection_scope == "NOT_GENERATED"
    assert summary.image_projection_status == "NOT_GENERATED"
    assert summary.professional_verdict_allowed is False
    assert summary.canonical_write_allowed is False


def test_private_reference_cannot_be_opened_by_an_unrelated_account() -> None:
    account_ref, case_ref = _reference_fixture()
    with engine.connect() as connection:
        unrelated = connection.execute(
            text(
                """
                SELECT account_ref
                FROM identity.accounts
                WHERE account_ref <> :account_ref
                ORDER BY account_ref
                LIMIT 1
                """
            ),
            {"account_ref": account_ref},
        ).scalar_one()

    with pytest.raises(MingliStageError, match="mingli_stage_subject_not_found"):
        MingliStageService(engine).project(
            account_ref=str(unrelated),
            subject_id=f"case:{case_ref}",
            stage_mode=MingliStageMode.NATAL_4,
        )
