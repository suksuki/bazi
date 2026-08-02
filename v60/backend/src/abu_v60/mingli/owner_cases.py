from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.engine import Engine

from abu_v60.identity import (
    IdentityProfileAdmissionService,
    ProfileAdmissionDefinition,
)
from abu_v60.mingli.admission import (
    MingliCaseAdmissionDefinition,
    MingliCaseAdmissionError,
    MingliCaseAdmissionService,
)
from abu_v60.mingli.calendar import (
    CALENDAR_ENGINE_VERSION,
    BirthInput,
)
from abu_v60.mingli.compiler import compile_birth_case
from abu_v60.provenance import content_hash, stable_ref


class OwnerCaseError(ValueError):
    pass


class OwnerCaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=80)
    gender: Literal["male", "female"]
    calendar_type: Literal["solar", "lunar"]
    birth_date: date
    birth_time: time
    birth_location: str = Field(min_length=1, max_length=160)
    timezone: str = Field(min_length=1, max_length=80)
    lunar_leap_month: bool = False
    true_solar_time_policy: Literal["not_applied"] = "not_applied"

    def birth_input(self) -> BirthInput:
        return BirthInput(
            calendar_type=self.calendar_type,
            birth_date=self.birth_date,
            birth_time=self.birth_time,
            timezone=self.timezone,
            lunar_leap_month=self.lunar_leap_month,
            true_solar_time_policy=self.true_solar_time_policy,
        )


class MingliOwnerCaseService:
    """Create and select one real owner Case through existing authority ports."""

    def __init__(
        self,
        engine: Engine,
        *,
        profiles: IdentityProfileAdmissionService | None = None,
        admissions: MingliCaseAdmissionService | None = None,
    ) -> None:
        self._engine = engine
        self._profiles = profiles or IdentityProfileAdmissionService()
        self._admissions = admissions or MingliCaseAdmissionService()

    def create(self, *, account_ref: str, payload: OwnerCaseInput) -> dict[str, object]:
        birth_input = payload.birth_input()
        identity = {
            "account_ref": account_ref,
            "display_name": payload.display_name.strip(),
            "gender": payload.gender,
            "birth_input": birth_input.model_dump(mode="json"),
            "birth_location": payload.birth_location.strip(),
        }
        profile_ref = stable_ref("v60-owner-profile", identity)
        case_ref = stable_ref(
            "v60-owner-case",
            {
                "account_ref": account_ref,
                "profile_ref": profile_ref,
                "birth_input_hash": birth_input.input_hash,
            },
        )
        profile_payload = {
            **birth_input.model_dump(mode="json"),
            "display_name": payload.display_name.strip(),
            "gender": payload.gender,
            "birth_location": payload.birth_location.strip(),
            "source_origin": "HUMAN_OWNER_DIRECT_INPUT",
        }
        profile = ProfileAdmissionDefinition(
            profile_ref=profile_ref,
            account_ref=account_ref,
            display_name=payload.display_name.strip(),
            gender=payload.gender,
            calendar_type=birth_input.calendar_type,
            birth_date=birth_input.birth_date,
            birth_time=birth_input.birth_time,
            birth_location=payload.birth_location.strip(),
            timezone=birth_input.timezone,
            source_ref=f"v60.owner-input:{case_ref}",
            source_hash=content_hash(profile_payload),
            input_payload=profile_payload,
        )
        compiled = compile_birth_case(
            case_ref=case_ref,
            birth_input=birth_input,
        )
        definition = MingliCaseAdmissionDefinition.from_compiled(
            compiled=compiled,
            case_ref=case_ref,
            owner_account_ref=account_ref,
            profile_ref=profile_ref,
            subject_kind="HUMAN_OWNER",
            birth_input_hash=birth_input.input_hash,
            algorithm_version=CALENDAR_ENGINE_VERSION,
            source_manifest={
                "source_origin": "HUMAN_OWNER_DIRECT_INPUT",
                "profile_ref": profile_ref,
                "calendar_engine_version": CALENDAR_ENGINE_VERSION,
                "llm_calls": 0,
            },
        )

        with self._engine.begin() as connection:
            self._profiles.admit(connection, definition=profile)
            self._admissions.activate_owner_case(
                connection,
                account_ref=account_ref,
                case_ref=case_ref,
                require_existing=False,
            )
            self._admissions.admit(connection, definition=definition)
        return {
            "case_ref": case_ref,
            "profile_ref": profile_ref,
            "active": True,
            "chart": dict(compiled.pillars),
        }

    def activate(self, *, account_ref: str, case_ref: str) -> dict[str, object]:
        try:
            with self._engine.begin() as connection:
                self._admissions.activate_owner_case(
                    connection,
                    account_ref=account_ref,
                    case_ref=case_ref,
                )
        except MingliCaseAdmissionError as exc:
            if str(exc) == "owner_case_not_found":
                raise OwnerCaseError("owner_case_not_found") from exc
            raise
        return {"case_ref": case_ref, "active": True}
