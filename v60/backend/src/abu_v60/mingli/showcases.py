from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any, Final

from sqlalchemy.engine import Engine

from abu_v60.identity import (
    AccountAdmissionDefinition,
    IdentityAdmissionDefinition,
    IdentityAdmissionService,
    ProfileAdmissionDefinition,
)
from abu_v60.identity.security import PBKDF2_SHA256_310K
from abu_v60.migration import MigrationBatchAdmissionService, MigrationBatchDefinition
from abu_v60.mingli.admission import (
    MingliCaseAdmissionDefinition,
    MingliCaseAdmissionService,
)
from abu_v60.mingli.calendar import (
    CALENDAR_ENGINE_VERSION,
    BirthInput,
    resolve_four_pillars,
)
from abu_v60.mingli.compiler import compile_birth_case
from abu_v60.provenance import content_hash

SHOWCASE_ACCOUNT_REF: Final = "v60-system-account-character-showcases-v1"
SHOWCASE_BATCH_REF: Final = "v60-seed-batch-mingli-character-showcases-v1"
ABU_PROFILE_REF: Final = "v60-synthetic-profile-abu-v1"
ABU_CASE_REF: Final = "v60-synthetic-case-abu-v1"
DUODUO_PROFILE_REF: Final = "v60-synthetic-profile-dodo-v1"
DUODUO_CASE_REF: Final = "v60-synthetic-case-dodo-v1"


@dataclass(frozen=True, slots=True)
class MingliShowcaseDefinition:
    subject_id: str
    case_ref: str
    profile_ref: str
    display_name: str
    gender: str
    birth_date: date
    birth_time: time
    birth_location: str
    source_ref: str
    character_ref: str
    narrator_actor_id: str
    expected_pillars: tuple[str, str, str, str]

    @property
    def birth_input(self) -> BirthInput:
        return BirthInput(
            calendar_type="solar",
            birth_date=self.birth_date,
            birth_time=self.birth_time,
            timezone="Asia/Shanghai",
            true_solar_time_policy="not_applied",
        )


SHOWCASES: Final = (
    MingliShowcaseDefinition(
        subject_id="abu",
        case_ref=ABU_CASE_REF,
        profile_ref=ABU_PROFILE_REF,
        display_name="阿布",
        gender="male",
        birth_date=date(1998, 11, 11),
        birth_time=time(12, 0),
        birth_location="北京",
        source_ref="v60.owner-canon:character-birth:abu:v1",
        character_ref="ABU_CHARACTER_V60_V1",
        narrator_actor_id="ABU_NARRATOR_V1",
        expected_pillars=("戊寅", "癸亥", "壬戌", "丙午"),
    ),
    MingliShowcaseDefinition(
        subject_id="duoduo",
        case_ref=DUODUO_CASE_REF,
        profile_ref=DUODUO_PROFILE_REF,
        display_name="多多",
        gender="female",
        birth_date=date(2001, 5, 8),
        birth_time=time(18, 0),
        birth_location="上海",
        source_ref="v60.owner-canon:character-birth:dodo:v1",
        character_ref="V60_DUODUO_SHOWCASE_V1",
        narrator_actor_id="DUODUO_NARRATOR_V1",
        expected_pillars=("辛巳", "癸巳", "辛未", "丁酉"),
    ),
)
SHOWCASE_BY_SUBJECT: Final = {item.subject_id: item for item in SHOWCASES}
SHOWCASE_BY_CASE: Final = {item.case_ref: item for item in SHOWCASES}


def seed_mingli_showcases(engine: Engine) -> dict[str, Any]:
    """Admit the two Owner-approved fictional character Cases idempotently."""

    manifest = {
        "seed_id": "v60.mingli-character-showcases.v1",
        "subject_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "calendar_type": "solar",
        "timezone": "Asia/Shanghai",
        "true_solar_time_policy": "not_applied",
        "case_refs": [item.case_ref for item in SHOWCASES],
        "llm_calls": 0,
    }
    with engine.begin() as connection:
        MigrationBatchAdmissionService().admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=SHOWCASE_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=manifest,
            ),
        )
        for definition in SHOWCASES:
            birth_input = definition.birth_input
            chart = resolve_four_pillars(birth_input)
            if tuple(chart.ordered()) != definition.expected_pillars:
                raise ValueError(f"showcase_pillar_drift:{definition.subject_id}")
            _admit_identity(connection, definition=definition)
            compiled = compile_birth_case(
                case_ref=definition.case_ref,
                birth_input=birth_input,
            )
            MingliCaseAdmissionService().admit(
                connection,
                definition=MingliCaseAdmissionDefinition.from_compiled(
                    compiled=compiled,
                    case_ref=definition.case_ref,
                    owner_account_ref=SHOWCASE_ACCOUNT_REF,
                    profile_ref=definition.profile_ref,
                    subject_kind="CANONICAL_SYNTHETIC",
                    birth_input_hash=birth_input.input_hash,
                    algorithm_version=CALENDAR_ENGINE_VERSION,
                    source_manifest={
                        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
                        "source_ref": definition.source_ref,
                        "seed_batch_ref": SHOWCASE_BATCH_REF,
                        "synthetic_identity": True,
                        "calendar_type": "solar",
                        "timezone": "Asia/Shanghai",
                        "true_solar_time_policy": "not_applied",
                        "llm_calls": 0,
                    },
                ),
            )
    return {
        "seed_batch_ref": SHOWCASE_BATCH_REF,
        "subject_kind": "CANONICAL_SYNTHETIC",
        "showcases": [
            {
                "subject_id": item.subject_id,
                "case_ref": item.case_ref,
                "profile_ref": item.profile_ref,
                "display_name": item.display_name,
                "pillars": list(item.expected_pillars),
            }
            for item in SHOWCASES
        ],
    }


def _admit_identity(connection: Any, *, definition: MingliShowcaseDefinition) -> None:
    account_identity = {
        "account_ref": SHOWCASE_ACCOUNT_REF,
        "purpose": "owner-approved fictional character showcases",
    }
    profile_payload = {
        **definition.birth_input.model_dump(mode="json"),
        "display_name": definition.display_name,
        "gender": definition.gender,
        "birth_location": definition.birth_location,
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_ref": definition.source_ref,
        "subject_kind": "CANONICAL_SYNTHETIC",
        "synthetic_identity": True,
        "owner_approved": True,
        "character_ref": definition.character_ref,
        "narrator_actor_id": definition.narrator_actor_id,
        "llm_calls": 0,
    }
    IdentityAdmissionService().admit(
        connection,
        definition=IdentityAdmissionDefinition(
            account=AccountAdmissionDefinition(
                account_ref=SHOWCASE_ACCOUNT_REF,
                email="mingli-character-showcases@v60.invalid",
                display_name="V60 Mingli Character Showcases",
                account_role="system_owner",
                active=False,
                password_scheme=PBKDF2_SHA256_310K,
                password_hash="0" * 64,
                password_salt="0" * 32,
                source_ref="v60.owner-canon:character-showcases:v1",
                source_hash=content_hash(account_identity),
                source_batch_ref=SHOWCASE_BATCH_REF,
            ),
            profile=ProfileAdmissionDefinition(
                profile_ref=definition.profile_ref,
                account_ref=SHOWCASE_ACCOUNT_REF,
                display_name=definition.display_name,
                gender=definition.gender,
                calendar_type="solar",
                birth_date=definition.birth_date,
                birth_time=definition.birth_time,
                birth_location=definition.birth_location,
                timezone="Asia/Shanghai",
                source_ref=definition.source_ref,
                source_hash=content_hash(profile_payload),
                input_payload=profile_payload,
            ),
        ),
    )
