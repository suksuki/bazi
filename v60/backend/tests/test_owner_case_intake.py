from __future__ import annotations

from collections.abc import Iterator
from datetime import date, time

import pytest
from abu_v60.db import engine
from abu_v60.dream.seed import SEED_BATCH_REF
from abu_v60.mingli.owner_cases import MingliOwnerCaseService, OwnerCaseInput
from abu_v60.provenance import content_hash
from sqlalchemy import text

ACCOUNT_REF = "v60-account-owner-case-intake-qa"


@pytest.fixture
def owner_account() -> Iterator[str]:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO identity.accounts
                    (account_ref, email, display_name, account_role, active,
                     password_scheme, password_hash, password_salt,
                     source_ref, source_hash, source_batch_ref)
                VALUES
                    (:account_ref, 'owner-case-intake@example.invalid',
                     'Owner Case Intake QA', 'test_operator', true,
                     'pbkdf2_sha256_310k', :password_hash, :password_salt,
                     'v60:test:owner-case-intake', :source_hash, :batch_ref)
                ON CONFLICT (account_ref) DO NOTHING
                """
            ),
            {
                "account_ref": ACCOUNT_REF,
                "password_hash": "0" * 64,
                "password_salt": "0" * 32,
                "source_hash": content_hash({"account_ref": ACCOUNT_REF}),
                "batch_ref": SEED_BATCH_REF,
            },
        )
    try:
        yield ACCOUNT_REF
    finally:
        with engine.begin() as connection:
            case_refs = list(
                connection.execute(
                    text(
                        """
                        SELECT case_ref
                        FROM mingli.cases
                        WHERE owner_account_ref = :account_ref
                        """
                    ),
                    {"account_ref": ACCOUNT_REF},
                ).scalars()
            )
            profile_refs = list(
                connection.execute(
                    text(
                        """
                        SELECT profile_ref
                        FROM identity.profiles
                        WHERE account_ref = :account_ref
                        """
                    ),
                    {"account_ref": ACCOUNT_REF},
                ).scalars()
            )
            if case_refs:
                for table in (
                    "canonical_scenes",
                    "life_case_revisions",
                    "facts",
                    "chart_versions",
                    "cases",
                ):
                    connection.execute(
                        text(
                            f"""
                            DELETE FROM mingli.{table}
                            WHERE case_ref = ANY(:case_refs)
                            """
                        ),
                        {"case_refs": case_refs},
                    )
            if profile_refs:
                connection.execute(
                    text(
                        """
                        DELETE FROM identity.profiles
                        WHERE profile_ref = ANY(:profile_refs)
                        """
                    ),
                    {"profile_refs": profile_refs},
                )
            connection.execute(
                text(
                    """
                    DELETE FROM identity.accounts
                    WHERE account_ref = :account_ref
                    """
                ),
                {"account_ref": ACCOUNT_REF},
            )


def _payload(name: str, day: int) -> OwnerCaseInput:
    return OwnerCaseInput(
        display_name=name,
        gender="male",
        calendar_type="solar",
        birth_date=date(1990, 6, day),
        birth_time=time(9, 30),
        birth_location="上海",
        timezone="Asia/Shanghai",
    )


def test_owner_can_create_switch_and_replay_real_compiled_cases(
    owner_account: str,
) -> None:
    service = MingliOwnerCaseService(engine)

    first = service.create(account_ref=owner_account, payload=_payload("甲", 12))
    replay = service.create(account_ref=owner_account, payload=_payload("甲", 12))
    second = service.create(account_ref=owner_account, payload=_payload("乙", 13))

    assert replay == first
    assert second["case_ref"] != first["case_ref"]
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT case_ref, status
                FROM mingli.cases
                WHERE owner_account_ref = :account_ref
                ORDER BY case_ref
                """
            ),
            {"account_ref": owner_account},
        ).mappings().all()
    assert len(rows) == 2
    assert {row["case_ref"] for row in rows if row["status"] == "ACTIVE"} == {
        second["case_ref"]
    }

    service.activate(account_ref=owner_account, case_ref=str(first["case_ref"]))
    with engine.connect() as connection:
        active = connection.execute(
            text(
                """
                SELECT case_ref
                FROM mingli.cases
                WHERE owner_account_ref = :account_ref
                  AND status = 'ACTIVE'
                """
            ),
            {"account_ref": owner_account},
        ).scalar_one()
    assert active == first["case_ref"]
