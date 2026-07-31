from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.engine import Engine

from abu_v60.dream.grove import (
    THREE_LIFE_POOL_REF,
    DreamGroveAdmissionService,
    GroveCandidateDefinition,
)
from abu_v60.dream.qualification_content import (
    THREE_LIFE_QUALIFICATION_SPECS,
    ThreeLifeQualificationSpec,
)
from abu_v60.dream.seed import SEED_BATCH_REF, SYSTEM_ACCOUNT_REF, seed_first_slice
from abu_v60.dream.tree_admission import LifeTreeAdmissionService, LifeTreeDefinition
from abu_v60.identity import (
    AccountAdmissionDefinition,
    IdentityAdmissionDefinition,
    IdentityAdmissionService,
    ProfileAdmissionDefinition,
)
from abu_v60.identity.security import PBKDF2_SHA256_310K
from abu_v60.migration import MigrationBatchAdmissionService, MigrationBatchDefinition
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
from abu_v60.mingli.compiler import CompiledCase, compile_case
from abu_v60.provenance import content_hash
from abu_v60.story import (
    QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
    EpisodeSourceCompilation,
    StoryEpisodeAdmissionService,
    StoryEpisodeTransitionAdmissionService,
    persisted_seed_episode_bindings,
    qualification_episode_source_registry,
)
from abu_v60.system_manifest import PRIMARY_WORLD_ID
from abu_v60.world import (
    WorldActorAdmissionService,
    WorldActorDefinition,
    WorldEventAdmissionService,
    WorldEventDefinition,
)

THREE_LIFE_SEED_BATCH_REF = "v60-seed-batch-three-life-qualification-v1"
THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF = (
    "v60-seed-batch-three-life-wenxi-chapter-two-v1"
)
THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF = (
    "v60-seed-batch-three-life-heyang-chapter-two-v1"
)
THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH = (
    "11a060ced3ae7413a99f9d2b3aaa41156aac5fbc05e27d54ba35b08a6a182b34"
)
WENXI_CHAPTER_TWO_SOURCE_REGISTRY_HASH = (
    "9c42166f63d97fb6608656f71077cc91283ef266b811e83b861f60b3cf7dacd8"
)
WENXI_CHAPTER_TWO_PACKAGE_REF = (
    "v60.episode-package.wenxi-index-convention.v1"
)
WENXI_CHAPTER_TWO_PACKAGE_HASH = (
    "6e0af51871d116eb5b9ed49e236b047b99bb4ae50b4767bab0ac8f216f466284"
)
WENXI_CHAPTER_TWO_QUESTION_REF = "v60-question-wenxi-index-convention-v1"
WENXI_CHAPTER_TWO_WORLD_EVENT_REF = (
    "v60-world-event-wenxi-index-adoption-v1"
)
WENXI_CHAPTER_TWO_TRANSITION_REF = (
    "v60-episode-transition-64b0804f1fdb3d1093fa"
)
WENXI_CHAPTER_TWO_TRANSITION_HASH = (
    "74d92439d60a74c41623951bfff4e73e52680959a8251d25e88aa70c78ee9fbe"
)
HEYANG_CHAPTER_TWO_PACKAGE_REF = (
    "v60.episode-package.heyang-delivery-settlement.v1"
)
HEYANG_CHAPTER_TWO_PACKAGE_HASH = (
    "56ec73713b30aeedba7614dd8ed9df26f23193b5c0c6499426c6dabbbe2e992a"
)
HEYANG_CHAPTER_TWO_QUESTION_REF = (
    "v60-question-heyang-delivery-settlement-v1"
)
HEYANG_CHAPTER_TWO_WORLD_EVENT_REF = (
    "v60-world-event-heyang-delivery-settlement-v1"
)
HEYANG_CHAPTER_TWO_TRANSITION_REF = (
    "v60-episode-transition-4a26813b25683563290a"
)
HEYANG_CHAPTER_TWO_TRANSITION_HASH = (
    "56b69403515aff0770bf8bff61e4e73ddaa1143d22643a0663b714d86d5ad254"
)
_CONTINUATION_PACKAGE_REFS = {
    "v60.episode-package.wenxi-archive-trial.v1": (
        WENXI_CHAPTER_TWO_PACKAGE_REF,
    ),
    "v60.episode-package.heyang-dyed-cloth.v1": (
        HEYANG_CHAPTER_TWO_PACKAGE_REF,
    ),
}


def seed_three_life_qualification(engine: Engine) -> dict[str, Any]:
    seed_first_slice(engine)
    prepared = tuple(_prepare_spec(spec) for spec in THREE_LIFE_QUALIFICATION_SPECS)
    seed_manifest = {
        "seed_id": "v60.dream-three-life-qualification.v1",
        "pool_ref": THREE_LIFE_POOL_REF,
        "actor_kind": "CANONICAL_SYNTHETIC",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_registry_hash": THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH,
        "llm_calls": 0,
        "case_refs": [item["spec"].case_ref for item in prepared],
        "question_refs": [
            item["source"].definition.runtime.question_ref for item in prepared
        ],
    }
    chapter_two_manifest = {
        "seed_id": "v60.dream-three-life-wenxi-chapter-two.v1",
        "parent_batch_ref": THREE_LIFE_SEED_BATCH_REF,
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_registry_hash": WENXI_CHAPTER_TWO_SOURCE_REGISTRY_HASH,
        "package_ref": WENXI_CHAPTER_TWO_PACKAGE_REF,
        "package_hash": WENXI_CHAPTER_TWO_PACKAGE_HASH,
        "question_ref": WENXI_CHAPTER_TWO_QUESTION_REF,
        "world_event_ref": WENXI_CHAPTER_TWO_WORLD_EVENT_REF,
        "transition_ref": WENXI_CHAPTER_TWO_TRANSITION_REF,
        "transition_hash": WENXI_CHAPTER_TWO_TRANSITION_HASH,
        "llm_calls": 0,
    }
    heyang_chapter_two_manifest = {
        "seed_id": "v60.dream-three-life-heyang-chapter-two.v1",
        "parent_batch_ref": THREE_LIFE_SEED_BATCH_REF,
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_registry_hash": QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
        "package_ref": HEYANG_CHAPTER_TWO_PACKAGE_REF,
        "package_hash": HEYANG_CHAPTER_TWO_PACKAGE_HASH,
        "question_ref": HEYANG_CHAPTER_TWO_QUESTION_REF,
        "world_event_ref": HEYANG_CHAPTER_TWO_WORLD_EVENT_REF,
        "transition_ref": HEYANG_CHAPTER_TWO_TRANSITION_REF,
        "transition_hash": HEYANG_CHAPTER_TWO_TRANSITION_HASH,
        "llm_calls": 0,
    }
    with engine.begin() as connection:
        batch_admission = MigrationBatchAdmissionService()
        batch_admission.admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=THREE_LIFE_SEED_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=seed_manifest,
            ),
        )
        batch_admission.admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=chapter_two_manifest,
            ),
        )
        batch_admission.admit(
            connection,
            definition=MigrationBatchDefinition(
                batch_ref=THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF,
                source_system="V60",
                source_database="qiazhi_v60",
                status="COMPLETED",
                manifest=heyang_chapter_two_manifest,
            ),
        )
        for item in prepared:
            _admit_prepared(connection, engine=engine, item=item)
        transition_admission = StoryEpisodeTransitionAdmissionService()
        for transition in qualification_episode_source_registry().transitions():
            transition_admission.admit(
                connection,
                definition=transition,
            )

    return {
        "pool_ref": THREE_LIFE_POOL_REF,
        "source_registry_hash": QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
        "legacy_source_registry_hash": THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH,
        "chapter_two_seed_batch_ref": THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF,
        "heyang_chapter_two_seed_batch_ref": (
            THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF
        ),
        "llm_calls": 0,
        "candidates": [
            {
                "actor_ref": item["spec"].actor_ref,
                "case_ref": item["spec"].case_ref,
                "tree_ref": item["spec"].tree_ref,
                "question_ref": item["source"].definition.runtime.question_ref,
                "domain": item["spec"].domain,
                "structure_fact_ref": item["structure_fact"]["fact_ref"],
                "life_domain_vector_ref": item["life_domain_vector"].vector_ref,
                "scene_ref": item["compiled"].scene_ref,
                "phenotype": item["compiled"].scene_payload["tree_phenotype"],
            }
            for item in prepared
        ],
    }


def _prepare_spec(spec: ThreeLifeQualificationSpec) -> dict[str, Any]:
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=spec.birth_date,
        birth_time=spec.birth_time,
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )
    compiled = compile_case(
        case_ref=spec.case_ref,
        birth_input=birth_input,
        chart=resolve_four_pillars(birth_input),
    )
    structure_fact = _select_structure_fact(compiled)
    quant_vector = MingliQuantFoundationCompiler().compile(
        case_ref=spec.case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    mechanism_vector = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant_vector,
        facts=compiled.facts,
    )
    timing_vector = MingliTimingEvidenceCompiler().compile(
        case_ref=spec.case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=compiled.life_case_revision_ref,
        birth_input=birth_input,
        gender=spec.gender,
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=date(2026, 7, 29),
        mechanism_vector=mechanism_vector,
    )
    life_domain_vector = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism_vector,
        timing_vector=timing_vector,
    )
    source_registry = qualification_episode_source_registry()
    bindings = {
        spec.binding_fact_key: structure_fact["fact_ref"],
        spec.binding_domain_key: life_domain_vector.vector_ref,
    }
    source = source_registry.compile_package(
        spec.package_ref,
        bindings=bindings,
    )
    if (
        source.definition.actor_ref != spec.actor_ref
        or source.definition.tree_ref != spec.tree_ref
        or not source.definition.runtime.entrypoint
    ):
        raise ValueError("three_life_qualification_source_identity_mismatch")
    continuation_sources = tuple(
        source_registry.compile_package(
            package_ref,
            bindings=bindings,
        )
        for package_ref in _CONTINUATION_PACKAGE_REFS.get(spec.package_ref, ())
    )
    if any(
        continuation.definition.actor_ref != spec.actor_ref
        or continuation.definition.tree_ref != spec.tree_ref
        or continuation.definition.runtime.entrypoint
        for continuation in continuation_sources
    ):
        raise ValueError("three_life_qualification_continuation_identity_mismatch")
    return {
        "spec": spec,
        "birth_input": birth_input,
        "compiled": compiled,
        "structure_fact": structure_fact,
        "quant_vector": quant_vector,
        "mechanism_vector": mechanism_vector,
        "timing_vector": timing_vector,
        "life_domain_vector": life_domain_vector,
        "bindings": bindings,
        "source": source,
        "continuation_sources": continuation_sources,
    }


def _select_structure_fact(compiled: CompiledCase) -> dict[str, Any]:
    for fact_type in ("six_harmony_membership", "hidden_stem_membership"):
        match = next(
            (fact for fact in compiled.facts if fact["fact_type"] == fact_type),
            None,
        )
        if match is not None:
            return match
    raise ValueError("three_life_qualification_structure_fact_missing")


def _admit_prepared(
    connection: Any,
    *,
    engine: Engine,
    item: dict[str, Any],
) -> None:
    spec: ThreeLifeQualificationSpec = item["spec"]
    birth_input: BirthInput = item["birth_input"]
    compiled: CompiledCase = item["compiled"]

    _admit_identity(connection, spec=spec, birth_input=birth_input)
    MingliCaseAdmissionService().admit(
        connection,
        definition=MingliCaseAdmissionDefinition.from_compiled(
            compiled=compiled,
            case_ref=spec.case_ref,
            owner_account_ref=SYSTEM_ACCOUNT_REF,
            profile_ref=spec.profile_ref,
            subject_kind="CANONICAL_SYNTHETIC",
            birth_input_hash=birth_input.input_hash,
            algorithm_version=CALENDAR_ENGINE_VERSION,
            source_manifest={
                "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
                "seed_batch_ref": THREE_LIFE_SEED_BATCH_REF,
                "source_registry_hash": THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH,
                "llm_calls": 0,
            },
        ),
    )
    MingliQuantVectorStore(engine).ensure_in_connection(
        connection,
        vector=item["quant_vector"],
    )
    MingliMechanismVectorStore(engine).ensure_in_connection(
        connection,
        vector=item["mechanism_vector"],
    )
    MingliTimingVectorStore(engine).ensure_in_connection(
        connection,
        vector=item["timing_vector"],
    )
    MingliLifeDomainVectorStore(engine).ensure_in_connection(
        connection,
        vector=item["life_domain_vector"],
    )
    source_registry = qualification_episode_source_registry()
    prepared_sources = (
        item["source"],
        *item["continuation_sources"],
    )
    replay_bindings = persisted_seed_episode_bindings(
        connection,
        sources=prepared_sources,
        bindings=item["bindings"],
    )
    source: EpisodeSourceCompilation = source_registry.compile_package(
        spec.package_ref,
        bindings=replay_bindings,
    )
    continuation_sources = tuple(
        source_registry.compile_package(
            package_ref,
            bindings=replay_bindings,
        )
        for package_ref in _CONTINUATION_PACKAGE_REFS.get(spec.package_ref, ())
    )
    _admit_actor(connection, spec=spec, source=source)
    _admit_world_events(connection, source=source)
    for continuation in continuation_sources:
        _admit_world_events(connection, source=continuation)
    LifeTreeAdmissionService().admit(
        connection,
        definition=LifeTreeDefinition(
            tree_ref=spec.tree_ref,
            actor_ref=spec.actor_ref,
            scene_ref=compiled.scene_ref,
            initial_state="DORMANT_QUESTION",
            organs=source.definition.model_dump(mode="json")["organ_set"],
        ),
    )
    StoryEpisodeAdmissionService().admit(
        connection,
        life_case_revision_ref=compiled.life_case_revision_ref,
        definition=source.definition,
    )
    for continuation in continuation_sources:
        StoryEpisodeAdmissionService().admit(
            connection,
            life_case_revision_ref=compiled.life_case_revision_ref,
            definition=continuation.definition,
        )
    DreamGroveAdmissionService().admit(
        connection,
        definition=GroveCandidateDefinition.issue(
            pool_ref=THREE_LIFE_POOL_REF,
            question_ref=source.definition.runtime.question_ref,
            actor_ref=spec.actor_ref,
            tree_ref=spec.tree_ref,
            domain=spec.domain,
            public_alias=spec.public_alias,
            premise=spec.premise,
            display_order=spec.display_order,
        ),
    )


def _admit_identity(
    connection: Any,
    *,
    spec: ThreeLifeQualificationSpec,
    birth_input: BirthInput,
) -> None:
    profile_payload = {
        **birth_input.model_dump(mode="json"),
        "display_name": spec.display_name,
        "synthetic_identity": True,
        "qualification_domain": spec.domain,
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
                profile_ref=spec.profile_ref,
                account_ref=SYSTEM_ACCOUNT_REF,
                display_name=spec.display_name,
                gender=spec.gender,
                calendar_type=birth_input.calendar_type,
                birth_date=birth_input.birth_date,
                birth_time=birth_input.birth_time,
                birth_location=spec.birth_location,
                timezone=birth_input.timezone,
                source_ref=f"v60.seed:three-life:{spec.domain}:v1",
                source_hash=content_hash(profile_payload),
                input_payload=profile_payload,
            ),
        ),
    )


def _admit_actor(
    connection: Any,
    *,
    spec: ThreeLifeQualificationSpec,
    source: EpisodeSourceCompilation,
) -> None:
    baseline_ref = source.definition.runtime.baseline_event_ref
    events = {
        definition.world_event_ref: definition
        for definition in source.world_event_definitions
    }
    baseline = events[baseline_ref]
    WorldActorAdmissionService().admit(
        connection,
        definition=WorldActorDefinition(
            actor_ref=spec.actor_ref,
            world_ref=PRIMARY_WORLD_ID,
            case_ref=spec.case_ref,
            actor_kind="CANONICAL_SYNTHETIC",
            display_name=spec.display_name,
            branch="canonical_world",
            initial_timeline={
                "timeline_version": 1,
                "events": [
                    {
                        "world_event_ref": baseline_ref,
                        "summary": baseline.event_payload["summary"],
                        "world_tick": baseline.due_tick,
                    }
                ],
                "privacy": "SYNTHETIC_CANONICAL_PUBLIC",
            },
            initial_state={
                "location": spec.location,
                "activity": spec.activity,
                "available": True,
            },
        ),
    )


def _admit_world_events(
    connection: Any,
    *,
    source: EpisodeSourceCompilation,
) -> None:
    service = WorldEventAdmissionService()
    definitions: dict[str, WorldEventDefinition] = {}
    for definition in source.world_event_definitions:
        existing = definitions.get(definition.world_event_ref)
        if existing is not None and existing != definition:
            raise ValueError("three_life_world_event_definition_conflict")
        definitions[definition.world_event_ref] = definition
    for definition in definitions.values():
        service.admit(connection, definition=definition)
