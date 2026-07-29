from __future__ import annotations

from datetime import date, time
from typing import Any

from sqlalchemy.engine import Engine

from abu_v60.dream.tree_admission import LifeTreeAdmissionService, LifeTreeDefinition
from abu_v60.identity import (
    AccountAdmissionDefinition,
    IdentityAdmissionDefinition,
    IdentityAdmissionService,
    ProfileAdmissionDefinition,
)
from abu_v60.identity.security import PBKDF2_SHA256_310K
from abu_v60.migration import (
    MigrationBatchAdmissionService,
    MigrationBatchDefinition,
)
from abu_v60.mingli import (
    MingliCaseAdmissionDefinition,
    MingliCaseAdmissionService,
    MingliLifeDomainEvidenceCompiler,
    MingliLifeDomainVectorStore,
    MingliMechanismEvidenceCompiler,
    MingliMechanismVectorStore,
    MingliQuantFoundationCompiler,
    MingliQuantVectorStore,
    MingliTimingEvidenceCompiler,
    MingliTimingVectorStore,
)
from abu_v60.mingli.calendar import CALENDAR_ENGINE_VERSION, BirthInput, resolve_four_pillars
from abu_v60.mingli.compiler import compile_case
from abu_v60.provenance import content_hash
from abu_v60.story import (
    EPISODE_SOURCE_REGISTRY_HASH,
    EpisodeSourceCompilation,
    StoryEpisodeAdmissionService,
    StoryEpisodeTransitionAdmissionService,
    default_episode_source_registry,
)
from abu_v60.system_manifest import PRIMARY_WORLD_ID
from abu_v60.world import (
    WorldActorAdmissionService,
    WorldActorDefinition,
    WorldEventAdmissionService,
    WorldEventDefinition,
)

SYSTEM_ACCOUNT_REF = "v60-system-account-world-v1"
SYNTHETIC_PROFILE_REF = "v60-synthetic-profile-yanzhou-v1"
SYNTHETIC_CASE_REF = "v60-synthetic-case-yanzhou-v1"
SEED_BATCH_REF = "v60-seed-batch-first-slice-v1"
SEED_EXTENSION_BATCH_REF = "v60-seed-batch-return-slice-v1"


def seed_first_slice(engine: Engine) -> dict[str, Any]:
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )
    chart = resolve_four_pillars(birth_input)
    compiled = compile_case(
        case_ref=SYNTHETIC_CASE_REF,
        birth_input=birth_input,
        chart=chart,
    )
    structure_fact = next(
        fact for fact in compiled.facts if fact["fact_type"] == "six_harmony_membership"
    )
    quant_vector = MingliQuantFoundationCompiler().compile(
        case_ref=SYNTHETIC_CASE_REF,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    mechanism_vector = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant_vector,
        facts=compiled.facts,
    )
    episode_timing_vector = MingliTimingEvidenceCompiler().compile(
        case_ref=SYNTHETIC_CASE_REF,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=compiled.life_case_revision_ref,
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=date(2026, 7, 29),
    )
    timing_vector = MingliTimingEvidenceCompiler().compile(
        case_ref=SYNTHETIC_CASE_REF,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=compiled.life_case_revision_ref,
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=date(2026, 7, 29),
        mechanism_vector=mechanism_vector,
    )
    life_domain_vector = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism_vector,
        timing_vector=timing_vector,
    )
    source_registry = default_episode_source_registry()
    source_packages = source_registry.compile_all(
        bindings={
            "structure_fact_ref": structure_fact["fact_ref"],
            "timing_vector_ref": episode_timing_vector.vector_ref,
            "life_domain_vector_ref": life_domain_vector.vector_ref,
        },
    )
    entry_sources = [source for source in source_packages if source.definition.runtime.entrypoint]
    if len(entry_sources) != 1:
        raise ValueError("episode_source_registry_requires_one_entrypoint")
    entry_source = entry_sources[0]
    first_episode = entry_source.definition
    entry_transitions = [
        transition
        for transition in source_registry.transitions()
        if transition.from_question_ref == first_episode.runtime.question_ref
    ]
    if len(entry_transitions) != 1:
        raise ValueError("episode_source_registry_entry_transition_invalid")
    return_question_ref = entry_transitions[0].to_question_ref
    return_sources = [
        source
        for source in source_packages
        if source.definition.runtime.question_ref == return_question_ref
    ]
    if len(return_sources) != 1:
        raise ValueError("episode_source_registry_return_episode_missing")
    return_episode = return_sources[0].definition
    world_events = _source_world_event_definitions(source_packages)

    seed_manifest = {
        "seed_id": "v60.first-dream-slice.yanzhou.v1",
        "actor_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "llm_calls": 0,
        "case_ref": SYNTHETIC_CASE_REF,
        "question_ref": first_episode.runtime.question_ref,
        "world_event_ref": first_episode.runtime.world_event_ref,
    }
    seed_extension_manifest = {
        "seed_id": "v60.return-dream-slice.yanzhou.v1",
        "parent_batch_ref": SEED_BATCH_REF,
        "actor_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "llm_calls": 0,
        "case_ref": SYNTHETIC_CASE_REF,
        "question_ref": return_episode.runtime.question_ref,
        "world_event_ref": return_episode.runtime.world_event_ref,
    }
    tree_organs = first_episode.model_dump(mode="json")["organ_set"]
    with engine.begin() as connection:
        _insert_seed_batches(connection, seed_manifest, seed_extension_manifest)
        _insert_system_identity(connection, birth_input)
        _insert_case_chain(connection, birth_input, compiled)
        MingliQuantVectorStore(engine).ensure_in_connection(
            connection,
            vector=quant_vector,
        )
        MingliMechanismVectorStore(engine).ensure_in_connection(
            connection,
            vector=mechanism_vector,
        )
        MingliTimingVectorStore(engine).ensure_in_connection(
            connection,
            vector=episode_timing_vector,
        )
        MingliTimingVectorStore(engine).ensure_in_connection(
            connection,
            vector=timing_vector,
        )
        MingliLifeDomainVectorStore(engine).ensure_in_connection(
            connection,
            vector=life_domain_vector,
        )
        _insert_actor(
            connection,
            actor_ref=first_episode.actor_ref,
            baseline_event_ref=first_episode.runtime.baseline_event_ref,
        )
        _admit_world_events(connection, definitions=world_events)
        _insert_tree(
            connection,
            compiled,
            tree_organs,
            tree_ref=first_episode.tree_ref,
            actor_ref=first_episode.actor_ref,
        )
        admission_service = StoryEpisodeAdmissionService()
        for source in source_packages:
            admission_service.admit(
                connection,
                life_case_revision_ref=compiled.life_case_revision_ref,
                definition=source.definition,
            )
        transition_service = StoryEpisodeTransitionAdmissionService()
        for transition in source_registry.transitions():
            transition_service.admit(connection, definition=transition)
    return {
        "actor_ref": first_episode.actor_ref,
        "case_ref": SYNTHETIC_CASE_REF,
        "tree_ref": first_episode.tree_ref,
        "question_ref": first_episode.runtime.question_ref,
        "return_question_ref": return_episode.runtime.question_ref,
        "world_event_ref": first_episode.runtime.world_event_ref,
        "return_world_event_ref": return_episode.runtime.world_event_ref,
        "episode_question_refs": [
            source.definition.runtime.question_ref for source in source_packages
        ],
        "episode_source_registry_hash": EPISODE_SOURCE_REGISTRY_HASH,
        "chart_version_ref": compiled.chart_version_ref,
        "life_case_revision_ref": compiled.life_case_revision_ref,
        "structure_fact_ref": structure_fact["fact_ref"],
        "timing_vector_ref": timing_vector.vector_ref,
        "episode_timing_vector_ref": episode_timing_vector.vector_ref,
        "life_domain_vector_ref": life_domain_vector.vector_ref,
    }


def _insert_seed_batches(
    connection: Any,
    seed_manifest: dict[str, Any],
    seed_extension_manifest: dict[str, Any],
) -> None:
    service = MigrationBatchAdmissionService()
    service.admit(
        connection,
        definition=MigrationBatchDefinition(
            batch_ref=SEED_BATCH_REF,
            source_system="V60",
            source_database="qiazhi_v60",
            status="COMPLETED",
            manifest=seed_manifest,
        ),
    )
    service.admit(
        connection,
        definition=MigrationBatchDefinition(
            batch_ref=SEED_EXTENSION_BATCH_REF,
            source_system="V60",
            source_database="qiazhi_v60",
            status="COMPLETED",
            manifest=seed_extension_manifest,
        ),
    )


def _insert_system_identity(connection: Any, birth_input: BirthInput) -> None:
    profile_payload = {
        **birth_input.model_dump(mode="json"),
        "display_name": "砚舟",
        "synthetic_identity": True,
    }
    IdentityAdmissionService().admit(
        connection,
        definition=IdentityAdmissionDefinition(
            account=AccountAdmissionDefinition(
                account_ref=SYSTEM_ACCOUNT_REF,
                email="world-system@v60.invalid",
                display_name="V60 World Authority",
                account_role="system_owner",
                active=False,
                password_scheme=PBKDF2_SHA256_310K,
                password_hash="0" * 64,
                password_salt="0" * 32,
                source_ref="v60.seed:yanzhou-v1",
                source_hash=content_hash({"system_account": SYSTEM_ACCOUNT_REF}),
                source_batch_ref=SEED_BATCH_REF,
            ),
            profile=ProfileAdmissionDefinition(
                profile_ref=SYNTHETIC_PROFILE_REF,
                account_ref=SYSTEM_ACCOUNT_REF,
                display_name="砚舟",
                gender="male",
                calendar_type=birth_input.calendar_type,
                birth_date=birth_input.birth_date,
                birth_time=birth_input.birth_time,
                birth_location="合成世界·南坡村",
                timezone=birth_input.timezone,
                source_ref="v60.seed:yanzhou-v1",
                source_hash=content_hash(profile_payload),
                input_payload=profile_payload,
            ),
        ),
    )


def _insert_case_chain(connection: Any, birth_input: BirthInput, compiled: Any) -> None:
    MingliCaseAdmissionService().admit(
        connection,
        definition=MingliCaseAdmissionDefinition.from_compiled(
            compiled=compiled,
            case_ref=SYNTHETIC_CASE_REF,
            owner_account_ref=SYSTEM_ACCOUNT_REF,
            profile_ref=SYNTHETIC_PROFILE_REF,
            subject_kind="CANONICAL_SYNTHETIC",
            birth_input_hash=birth_input.input_hash,
            algorithm_version=CALENDAR_ENGINE_VERSION,
            source_manifest={
                "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
                "seed_batch_ref": SEED_BATCH_REF,
                "llm_calls": 0,
            },
        ),
    )


def _insert_actor(
    connection: Any,
    *,
    actor_ref: str,
    baseline_event_ref: str,
) -> None:
    timeline = {
        "timeline_version": 1,
        "events": [
            {
                "world_event_ref": baseline_event_ref,
                "summary": "砚舟将引水草放回旧水渠，渠口重新出现浅水痕。",
                "world_tick": 0,
            }
        ],
        "privacy": "SYNTHETIC_CANONICAL_PUBLIC",
    }
    state = {
        "location": "south-slope-old-channel",
        "activity": "observing-restored-channel",
        "available": True,
    }
    WorldActorAdmissionService().admit(
        connection,
        definition=WorldActorDefinition(
            actor_ref=actor_ref,
            world_ref=PRIMARY_WORLD_ID,
            case_ref=SYNTHETIC_CASE_REF,
            actor_kind="CANONICAL_SYNTHETIC",
            display_name="砚舟",
            branch="canonical_world",
            initial_timeline=timeline,
            initial_state=state,
        ),
    )


def _admit_world_events(
    connection: Any,
    *,
    definitions: tuple[WorldEventDefinition, ...],
) -> None:
    service = WorldEventAdmissionService()
    for definition in definitions:
        service.admit(connection, definition=definition)


def first_slice_world_event_definitions() -> tuple[WorldEventDefinition, ...]:
    source_packages = default_episode_source_registry().compile_all(
        bindings={
            "structure_fact_ref": "v60-fact-structure-event-contract-probe",
            "timing_vector_ref": "v60-timing-vector-event-contract-probe",
            "life_domain_vector_ref": "v60-life-domain-vector-event-contract-probe",
        },
    )
    return _source_world_event_definitions(source_packages)


def _source_world_event_definitions(
    source_packages: tuple[EpisodeSourceCompilation, ...],
) -> tuple[WorldEventDefinition, ...]:
    definitions: dict[str, WorldEventDefinition] = {}
    for source in source_packages:
        for definition in source.world_event_definitions:
            existing = definitions.get(definition.world_event_ref)
            if existing is not None and existing != definition:
                raise ValueError("episode_source_world_event_definition_conflict")
            definitions.setdefault(definition.world_event_ref, definition)
    return tuple(definitions.values())


def _insert_tree(
    connection: Any,
    compiled: Any,
    organs: dict[str, Any],
    *,
    tree_ref: str,
    actor_ref: str,
) -> None:
    LifeTreeAdmissionService().admit(
        connection,
        definition=LifeTreeDefinition(
            tree_ref=tree_ref,
            actor_ref=actor_ref,
            scene_ref=compiled.scene_ref,
            initial_state="DORMANT_QUESTION",
            organs=organs,
        ),
    )
