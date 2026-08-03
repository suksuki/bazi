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
    FIRST_SYNTHETIC_EXPERIMENT,
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    SYNTHETIC_RESEARCH_BATCH_REF,
    SyntheticExperimentDefinition,
    resolve_synthetic_experiment,
)
from abu_v60.provenance import content_hash


def seed_first_synthetic_experiment(engine: Engine) -> dict[str, Any]:
    return seed_synthetic_experiment(
        engine,
        experiment_ref=FIRST_SYNTHETIC_EXPERIMENT_REF,
    )


def seed_synthetic_experiment(
    engine: Engine,
    *,
    experiment_ref: str,
) -> dict[str, Any]:
    """Admit one real-calendar pair, then build its shared evidence chain."""

    experiment = resolve_synthetic_experiment(experiment_ref)
    _ensure_research_account_batch(engine)
    return _seed_experiment(engine, experiment=experiment)


def _seed_experiment(
    engine: Engine,
    *,
    experiment: SyntheticExperimentDefinition,
) -> dict[str, Any]:
    members = experiment.members

    manifest = _experiment_manifest(experiment)
    with engine.begin() as connection:
        MigrationBatchAdmissionService().admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=experiment.seed_batch_ref,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=manifest,
            ),
        )
        for member in members:
            resolved = resolve_four_pillars(member.birth_input)
            if tuple(resolved.ordered()) != member.expected_pillars:
                raise ValueError(f"synthetic_experiment_calendar_drift:{member.member_ref}")
            _admit_identity(connection, member=member, experiment=experiment)
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
                        "experiment_ref": experiment.experiment_ref,
                        "member_ref": member.member_ref,
                        "variant": member.variant,
                        "seed_batch_ref": experiment.seed_batch_ref,
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
            analysis_date=experiment.analysis_date,
        )
        for member in members
    )
    return {
        "seed_batch_ref": experiment.seed_batch_ref,
        "experiment_ref": experiment.experiment_ref,
        "analysis_date": experiment.analysis_date.isoformat(),
        "members": list(materialized),
    }


def _experiment_manifest(
    experiment: SyntheticExperimentDefinition,
) -> dict[str, object]:
    return {
        "seed_id": experiment.seed_id,
        "experiment_ref": experiment.experiment_ref,
        "subject_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_CONTROLLED_SYNTHETIC_RESEARCH",
        "calendar_engine_version": CALENDAR_ENGINE_VERSION,
        "case_refs": [item.case_ref for item in experiment.members],
        "gold_in_seed": False,
        "llm_calls": 0,
    }


def _ensure_research_account_batch(engine: Engine) -> None:
    """Admit the account's original source batch without seeding its cases."""

    with engine.begin() as connection:
        MigrationBatchAdmissionService().admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=SYNTHETIC_RESEARCH_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=_experiment_manifest(FIRST_SYNTHETIC_EXPERIMENT),
            ),
        )


def _admit_identity(
    connection: Any,
    *,
    member: Any,
    experiment: SyntheticExperimentDefinition,
) -> None:
    account_identity = {
        "account_ref": SYNTHETIC_RESEARCH_ACCOUNT_REF,
        "purpose": "controlled synthetic Mingli Lab experiments",
    }
    source_ref = f"v60.synthetic-lab:{experiment.experiment_ref}:{member.variant}"
    profile_payload = {
        **member.birth_input.model_dump(mode="json"),
        "display_name": member.display_name,
        "gender": "male",
        "birth_location": "合成研究坐标",
        "source_origin": "V60_CONTROLLED_SYNTHETIC_RESEARCH",
        "experiment_ref": experiment.experiment_ref,
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
