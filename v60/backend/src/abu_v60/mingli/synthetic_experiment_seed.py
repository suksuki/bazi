from __future__ import annotations

from typing import Any

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
from abu_v60.mingli.calendar import CALENDAR_ENGINE_VERSION, resolve_four_pillars
from abu_v60.mingli.compiler import compile_birth_case
from abu_v60.mingli.materialization import MingliCaseMaterializationService
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_MEMBERS,
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    SYNTHETIC_RESEARCH_BATCH_REF,
)
from abu_v60.provenance import content_hash


def seed_first_synthetic_experiment(engine: Engine) -> dict[str, Any]:
    """Admit two real-calendar research Cases, then build their shared evidence chain."""

    manifest = {
        "seed_id": "v60.mingli-synthetic-lab.first-pair.001",
        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
        "subject_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_CONTROLLED_SYNTHETIC_RESEARCH",
        "calendar_engine_version": CALENDAR_ENGINE_VERSION,
        "case_refs": [item.case_ref for item in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS],
        "gold_in_seed": False,
        "llm_calls": 0,
    }
    with engine.begin() as connection:
        MigrationBatchAdmissionService().admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=SYNTHETIC_RESEARCH_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=manifest,
            ),
        )
        for member in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS:
            resolved = resolve_four_pillars(member.birth_input)
            if tuple(resolved.ordered()) != member.expected_pillars:
                raise ValueError(f"synthetic_experiment_calendar_drift:{member.member_ref}")
            _admit_identity(connection, member=member)
            compiled = compile_birth_case(
                case_ref=member.case_ref,
                birth_input=member.birth_input,
            )
            MingliCaseAdmissionService().admit(
                connection,
                definition=MingliCaseAdmissionDefinition.from_compiled(
                    compiled=compiled,
                    case_ref=member.case_ref,
                    owner_account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                    profile_ref=member.profile_ref,
                    subject_kind="CANONICAL_SYNTHETIC",
                    birth_input_hash=member.birth_input.input_hash,
                    algorithm_version=CALENDAR_ENGINE_VERSION,
                    source_manifest={
                        "source_origin": "V60_CONTROLLED_SYNTHETIC_RESEARCH",
                        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
                        "member_ref": member.member_ref,
                        "variant": member.variant,
                        "seed_batch_ref": SYNTHETIC_RESEARCH_BATCH_REF,
                        "synthetic_identity": True,
                        "gold_in_case": False,
                        "llm_calls": 0,
                    },
                ),
            )
    materializer = MingliCaseMaterializationService(engine)
    materialized = tuple(
        materializer.materialize(
            account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            case_ref=member.case_ref,
            subject_kind="CANONICAL_SYNTHETIC",
            analysis_date=SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
        )
        for member in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
    )
    return {
        "seed_batch_ref": SYNTHETIC_RESEARCH_BATCH_REF,
        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
        "analysis_date": SYNTHETIC_EXPERIMENT_ANALYSIS_DATE.isoformat(),
        "members": list(materialized),
    }


def _admit_identity(connection: Any, *, member: Any) -> None:
    account_identity = {
        "account_ref": SYNTHETIC_RESEARCH_ACCOUNT_REF,
        "purpose": "controlled synthetic Mingli Lab experiments",
    }
    source_ref = f"v60.synthetic-lab:{FIRST_SYNTHETIC_EXPERIMENT_REF}:{member.variant}"
    profile_payload = {
        **member.birth_input.model_dump(mode="json"),
        "display_name": member.display_name,
        "gender": "male",
        "birth_location": "合成研究坐标",
        "source_origin": "V60_CONTROLLED_SYNTHETIC_RESEARCH",
        "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
        "member_ref": member.member_ref,
        "variant": member.variant,
        "subject_kind": "CANONICAL_SYNTHETIC",
        "synthetic_identity": True,
        "gold_in_profile": False,
    }
    IdentityAdmissionService().admit(
        connection,
        definition=IdentityAdmissionDefinition(
            account=AccountAdmissionDefinition(
                account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                email="mingli-synthetic-lab@v60.invalid",
                display_name="V60 Mingli Synthetic Lab",
                account_role="system_owner",
                active=False,
                password_scheme=PBKDF2_SHA256_310K,
                password_hash="0" * 64,
                password_salt="0" * 32,
                source_ref="v60.synthetic-lab:account:v1",
                source_hash=content_hash(account_identity),
                source_batch_ref=SYNTHETIC_RESEARCH_BATCH_REF,
            ),
            profile=ProfileAdmissionDefinition(
                profile_ref=member.profile_ref,
                account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                display_name=member.display_name,
                gender="male",
                calendar_type="solar",
                birth_date=member.birth_input.birth_date,
                birth_time=member.birth_input.birth_time,
                birth_location="合成研究坐标",
                timezone=member.birth_input.timezone,
                source_ref=source_ref,
                source_hash=content_hash(profile_payload),
                input_payload=profile_payload,
            ),
        ),
    )
