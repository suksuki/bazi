from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.experience import HomeExperienceService
from abu_v60.mingli import MingliQuantVectorStore, MingliReadingStore
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def _human_owner_account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT DISTINCT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    ORDER BY owner_account_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )


def test_home_materializes_one_append_only_profile_pinned_reading() -> None:
    service = HomeExperienceService(engine)
    first = service.snapshot(account_ref=_human_owner_account_ref())
    second = service.snapshot(account_ref=_human_owner_account_ref())
    expected = first["mingli"]["reading"]

    assert second["mingli"]["reading"] == expected
    persisted = MingliReadingStore(engine).get(
        reading_ref=str(expected["reading_ref"])
    )
    assert persisted.model_dump(mode="json") == expected
    quant = first["mingli"]["quant_foundation"]
    persisted_vector = MingliQuantVectorStore(engine).get(
        vector_ref=str(quant["vector_ref"])
    )
    assert persisted_vector.model_dump(mode="json") == quant
    with engine.connect() as connection:
        count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM mingli.readings
                WHERE reading_ref = :reading_ref
                """
            ),
            {"reading_ref": expected["reading_ref"]},
        ).scalar_one()
    assert count == 1


def test_quant_vector_is_append_only_and_idempotent() -> None:
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=_human_owner_account_ref()
    )
    quant = snapshot["mingli"]["quant_foundation"]

    with engine.connect() as connection:
        count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM mingli.quant_foundation_vectors
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": quant["vector_ref"]},
        ).scalar_one()
    assert count == 1

    with (
        pytest.raises(DBAPIError, match="mingli_quant_vectors_are_append_only"),
        engine.begin() as connection,
    ):
        connection.execute(
            text(
                """
                UPDATE mingli.quant_foundation_vectors
                SET vector_version = 'forbidden-rewrite'
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": quant["vector_ref"]},
        )


def test_persisted_reading_rejects_rewrite_and_remains_replayable() -> None:
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=_human_owner_account_ref()
    )
    expected = snapshot["mingli"]["reading"]

    with (
        pytest.raises(DBAPIError, match="mingli_readings_are_append_only"),
        engine.begin() as connection,
    ):
        connection.execute(
            text(
                """
                UPDATE mingli.readings
                SET reading_version = 'forbidden-rewrite'
                WHERE reading_ref = :reading_ref
                """
            ),
            {"reading_ref": expected["reading_ref"]},
        )

    persisted = MingliReadingStore(engine).get(
        reading_ref=str(expected["reading_ref"])
    )
    assert persisted.model_dump(mode="json") == expected
