from __future__ import annotations

from datetime import date, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.provenance import canonical_json


class IdentityAdmissionError(ValueError):
    pass


class AccountAdmissionDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    account_ref: str = Field(min_length=1)
    email: str = Field(min_length=3)
    display_name: str = Field(min_length=1)
    account_role: str = Field(min_length=1)
    active: bool
    password_scheme: str = Field(min_length=1)
    password_hash: str = Field(min_length=1)
    password_salt: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_hash: str = Field(min_length=64, max_length=64)
    source_batch_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def email_is_normalized(self) -> AccountAdmissionDefinition:
        if self.email != self.email.strip().lower():
            raise ValueError("identity_account_email_must_be_normalized")
        return self


class ProfileAdmissionDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_ref: str = Field(min_length=1)
    account_ref: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    gender: str = Field(min_length=1)
    calendar_type: str = Field(min_length=1)
    birth_date: date
    birth_time: time
    birth_location: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_hash: str = Field(min_length=64, max_length=64)
    input_payload: dict[str, Any]
    active: bool = True


class IdentityAdmissionDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    account: AccountAdmissionDefinition
    profile: ProfileAdmissionDefinition

    @model_validator(mode="after")
    def profile_belongs_to_account(self) -> IdentityAdmissionDefinition:
        if self.profile.account_ref != self.account.account_ref:
            raise ValueError("identity_profile_account_mismatch")
        return self


class IdentityAdmissionService:
    """Identity-owned idempotent port for account/profile provisioning."""

    def admit(
        self,
        connection: Any,
        *,
        definition: IdentityAdmissionDefinition,
    ) -> None:
        account = definition.account
        profile = definition.profile
        connection.execute(
            text(
                """
                INSERT INTO identity.accounts
                    (account_ref, email, display_name, account_role, active,
                     password_scheme, password_hash, password_salt,
                     source_ref, source_hash, source_batch_ref)
                VALUES
                    (:account_ref, :email, :display_name, :account_role, :active,
                     :password_scheme, :password_hash, :password_salt,
                     :source_ref, :source_hash, :source_batch_ref)
                ON CONFLICT (account_ref) DO NOTHING
                """
            ),
            account.model_dump(mode="python"),
        )
        connection.execute(
            text(
                """
                INSERT INTO identity.profiles
                    (profile_ref, account_ref, display_name, gender, calendar_type,
                     birth_date, birth_time, birth_location, timezone,
                     source_ref, source_hash, input_json, active)
                VALUES
                    (:profile_ref, :account_ref, :display_name, :gender, :calendar_type,
                     :birth_date, :birth_time, :birth_location, :timezone,
                     :source_ref, :source_hash, CAST(:input_json AS jsonb), :active)
                ON CONFLICT (profile_ref) DO NOTHING
                """
            ),
            {
                **profile.model_dump(mode="python", exclude={"input_payload"}),
                "input_json": canonical_json(profile.input_payload),
            },
        )
        self._verify(connection, definition=definition)

    @staticmethod
    def _verify(
        connection: Any,
        *,
        definition: IdentityAdmissionDefinition,
    ) -> None:
        account = (
            connection.execute(
                text(
                    """
                    SELECT account_ref, source_ref, source_hash, source_batch_ref
                    FROM identity.accounts
                    WHERE account_ref = :account_ref
                    """
                ),
                {"account_ref": definition.account.account_ref},
            )
            .mappings()
            .one()
        )
        profile = (
            connection.execute(
                text(
                    """
                    SELECT profile_ref, account_ref, source_ref, source_hash, input_json
                    FROM identity.profiles
                    WHERE profile_ref = :profile_ref
                    """
                ),
                {"profile_ref": definition.profile.profile_ref},
            )
            .mappings()
            .one()
        )
        expected_account = {
            "account_ref": definition.account.account_ref,
            "source_ref": definition.account.source_ref,
            "source_hash": definition.account.source_hash,
            "source_batch_ref": definition.account.source_batch_ref,
        }
        expected_profile = {
            "profile_ref": definition.profile.profile_ref,
            "account_ref": definition.account.account_ref,
            "source_ref": definition.profile.source_ref,
            "source_hash": definition.profile.source_hash,
            "input_json": definition.profile.input_payload,
        }
        if dict(account) != expected_account or dict(profile) != expected_profile:
            raise IdentityAdmissionError("identity_admission_conflict")


class IdentityProfileAdmissionService:
    """Identity-owned idempotent port for profiles under an existing account."""

    def admit(
        self,
        connection: Any,
        *,
        definition: ProfileAdmissionDefinition,
    ) -> None:
        account_exists = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM identity.accounts
                    WHERE account_ref = :account_ref
                      AND active = true
                )
                """
            ),
            {"account_ref": definition.account_ref},
        ).scalar_one()
        if not account_exists:
            raise IdentityAdmissionError("identity_profile_account_not_active")

        connection.execute(
            text(
                """
                INSERT INTO identity.profiles
                    (profile_ref, account_ref, display_name, gender, calendar_type,
                     birth_date, birth_time, birth_location, timezone,
                     source_ref, source_hash, input_json, active)
                VALUES
                    (:profile_ref, :account_ref, :display_name, :gender, :calendar_type,
                     :birth_date, :birth_time, :birth_location, :timezone,
                     :source_ref, :source_hash, CAST(:input_json AS jsonb), :active)
                ON CONFLICT (profile_ref) DO NOTHING
                """
            ),
            {
                **definition.model_dump(mode="python", exclude={"input_payload"}),
                "input_json": canonical_json(definition.input_payload),
            },
        )
        profile = (
            connection.execute(
                text(
                    """
                    SELECT profile_ref, account_ref, display_name, gender, calendar_type,
                           birth_date, birth_time, birth_location, timezone,
                           source_ref, source_hash, input_json, active
                    FROM identity.profiles
                    WHERE profile_ref = :profile_ref
                    """
                ),
                {"profile_ref": definition.profile_ref},
            )
            .mappings()
            .one()
        )
        expected = {
            **definition.model_dump(mode="python", exclude={"input_payload"}),
            "input_json": definition.input_payload,
        }
        if dict(profile) != expected:
            raise IdentityAdmissionError("identity_profile_admission_conflict")
