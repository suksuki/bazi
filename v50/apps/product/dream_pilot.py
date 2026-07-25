from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from core.contracts import BirthInputCanonical
from core.contracts.professional_review import ProfessionalReviewOverlay
from core.engines import resolve_birth_input_pillars
from core.life_case import (
    FormalInsight,
    InsightBasis,
    InsightProvenance,
    InsightUncertainty,
    LifeCase,
    ReasoningPathStep,
    commit_baseline_life_case,
)
from core.mingli_agent import compile_chart_world
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    DiscriminatingProbe,
    EpistemicReviewReceipt,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    WorkPathReasoning,
)
from experience.dream import DREAM_PRIVACY_POLICY_VERSION, DreamSceneGrant
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner
from product.dream_store_contracts import DreamStore


DREAM_PILOT_NPC_POLICY_VERSION = "deepbazi.dream_pilot_npc_genesis.v1"
DREAM_PILOT_HUMAN_PROJECTION_POLICY_VERSION = (
    "deepbazi.dream_pilot_human_projection.v1"
)


@dataclass(frozen=True)
class CanonicalNpcSeed:
    npc_id: str
    case_id: str
    display_name: str
    gender: str
    birth_date: str
    birth_time: str
    birth_location: str
    timezone: str


CANONICAL_NPC_SEEDS = (
    CanonicalNpcSeed(
        npc_id="npc-mist-lan-v1",
        case_id="dream-pilot-npc-case-mist-lan-v1",
        display_name="雾岚",
        gender="female",
        birth_date="1992-03-17",
        birth_time="09:20",
        birth_location="杭州",
        timezone="Asia/Shanghai",
    ),
    CanonicalNpcSeed(
        npc_id="npc-ridge-zhou-v1",
        case_id="dream-pilot-npc-case-ridge-zhou-v1",
        display_name="砚舟",
        gender="male",
        birth_date="1987-10-29",
        birth_time="18:40",
        birth_location="首尔",
        timezone="Asia/Seoul",
    ),
)
CANONICAL_NPC_IDS = frozenset(item.npc_id for item in CANONICAL_NPC_SEEDS)


@dataclass(frozen=True)
class CanonicalNpcBootstrapResult:
    npc_id: str
    case_id: str
    life_case_id: str
    public_scene_ref: str
    genesis_manifest_hash: str
    created: bool
    grant_active: bool


class DreamCanonicalNpcBootstrapService:
    """Create the two projection-only residents without a second Case authority."""

    def __init__(self, *, case_store: AgentCaseStore, dream_store: DreamStore) -> None:
        self.case_store = case_store
        self.dream_store = dream_store
        self.scene_owner = CanonicalSceneOwner(case_store=case_store)

    def ensure(self) -> list[CanonicalNpcBootstrapResult]:
        return [self._ensure_one(seed) for seed in CANONICAL_NPC_SEEDS]

    def _ensure_one(self, seed: CanonicalNpcSeed) -> CanonicalNpcBootstrapResult:
        manifest = _genesis_manifest(seed)
        manifest_hash = _canonical_hash(manifest)
        existing = self.case_store.get(case_id=seed.case_id)
        created = existing is None
        if existing is None:
            row = self._build_case(seed=seed, manifest=manifest, manifest_hash=manifest_hash)
            self.case_store.save(
                case_id=seed.case_id,
                user_id=None,
                profile_id=None,
                payload=row,
            )
        else:
            row = existing
            _validate_existing_npc(
                row=row,
                seed=seed,
                manifest_hash=manifest_hash,
            )

        life_case = row.get("life_case") if isinstance(row.get("life_case"), dict) else {}
        life_case_id = str(life_case.get("life_case_id") or "")
        if not life_case_id:
            raise ValueError(f"canonical_npc_life_case_missing:{seed.npc_id}")

        grant_id, public_scene_ref = _npc_grant_identity(seed.npc_id)
        scene = self.scene_owner.issue_authorized_scene(
            case_id=seed.case_id,
            authorization_ref=grant_id,
            account_role="member",
        )
        current = self.dream_store.get_grant(public_scene_ref=public_scene_ref)
        now = datetime.now(timezone.utc)
        if current is None:
            current = self.dream_store.save_grant(DreamSceneGrant(
                grant_id=grant_id,
                case_id=seed.case_id,
                public_scene_ref=public_scene_ref,
                authorization_basis="canonical_npc_genesis_projection_only",
                authorized_by_ref="world-governance:dream-pilot-v1",
                authorization_version=DREAM_PILOT_NPC_POLICY_VERSION,
                subject_kind="canonical_npc",
                subject_ref=seed.npc_id,
                anonymization_policy_version=DREAM_PRIVACY_POLICY_VERSION,
                authorized_source_hash=scene.identity.source_hash,
                valid_from=now,
                created_at=now,
                updated_at=now,
            ))
        else:
            if (
                current.case_id != seed.case_id
                or current.subject_kind != "canonical_npc"
                or current.subject_ref != seed.npc_id
                or current.authorized_source_hash != scene.identity.source_hash
            ):
                raise ValueError(f"canonical_npc_grant_conflict:{seed.npc_id}")

        return CanonicalNpcBootstrapResult(
            npc_id=seed.npc_id,
            case_id=seed.case_id,
            life_case_id=life_case_id,
            public_scene_ref=public_scene_ref,
            genesis_manifest_hash=manifest_hash,
            created=created,
            grant_active=current.is_active_at(now),
        )

    def _build_case(
        self,
        *,
        seed: CanonicalNpcSeed,
        manifest: dict[str, Any],
        manifest_hash: str,
    ) -> dict[str, Any]:
        birth = resolve_birth_input_pillars(BirthInputCanonical(
            birth_input_id=f"canonical-npc-birth:{seed.npc_id}",
            name=seed.display_name,
            gender=seed.gender,
            calendar_type="solar",
            birth_date=seed.birth_date,
            birth_time=seed.birth_time,
            birth_location=seed.birth_location,
            timezone=seed.timezone,
            input_quality="canonical_npc_genesis",
        ))
        world = compile_chart_world(
            reading_id=f"canonical-npc-world:{seed.npc_id}",
            birth_input=birth,
            analysis_year=2026,
        )
        evidence_ref = next(
            (item.fact_id for item in world.facts if item.kind == "fact" and item.category == "pillars"),
            world.allowed_evidence_refs[0],
        )
        now = datetime.now(timezone.utc).isoformat()
        claim = "这棵树只投影正式历法确认的四柱；当前暂无已确认主路径。"
        source_record_id = f"canonical-npc-genesis:{seed.npc_id}"
        raw_hash = _canonical_hash({"claim": claim, "manifest_hash": manifest_hash})
        overlay = ProfessionalReviewOverlay(
            overlay_id=f"review-{source_record_id}",
            cognitive_record_ref=source_record_id,
            review_version="deterministic_npc_chart_only.v1",
            assertions_hash=_canonical_hash([]),
            raw_output_hash=raw_hash,
            raw_source_kind="deterministic_system_payload",
            persistence_status="persisted",
            professional_release_status="partially_blocked",
            reviewer="deterministic-npc-bootstrap",
            created_at=now,
        )
        insight = FormalInsight(
            insight_id=f"insight-{source_record_id}",
            case_id=seed.case_id,
            case_version="v1",
            type="baseline",
            claim=claim,
            scope={"temporal_scope": "natal", "projection_boundary": "chart_facts_only"},
            basis=InsightBasis(chart_fact_refs=[evidence_ref]),
            reasoning_path=[ReasoningPathStep(
                premise="四柱由 CanonicalTemporalService 从固定出生事实确定性生成。",
                conclusion="本轮只允许生成只读生命树与同源命盘镜。",
                source_refs=[evidence_ref],
            )],
            conditions=["仅限 DREAM-PILOT-01 封闭只读投影"],
            counter_signals=["任何专业路径或现实人生叙事均不在本轮授权范围"],
            uncertainty=InsightUncertainty(
                level="high",
                reasons=["尚未进行专业路径认知，不得从自然语言或潜在关系猜线。"],
            ),
            provenance=InsightProvenance(
                reasoner_id="deterministic.dream_npc_genesis",
                reasoner_version=DREAM_PILOT_NPC_POLICY_VERSION,
                theory_version="v50.canonical.chart_facts",
                model_version="none",
                context_hash=manifest_hash,
                generated_at=now,
                source_record_id=source_record_id,
            ),
            status="reviewed",
            persistence_status="persisted",
            professional_release_status="partially_blocked",
            professional_review_overlay=overlay,
            epistemic_state="reliable",
            source_review_gate="deterministic_npc_chart_only.v1",
            projection_payload={
                "identity_class": "canonical_npc",
                "professional_path_state": "unavailable_unconfirmed",
            },
        )
        life_case, receipt = commit_baseline_life_case(
            insight=insight,
            world=world,
            profile_id=None,
        )
        if not receipt.passed or life_case.relation_assertions or life_case.path_assertions:
            raise ValueError(f"canonical_npc_chart_only_boundary_failed:{seed.npc_id}")
        record = MingliCognitiveRecord(
            record_id=source_record_id,
            case_id=seed.case_id,
            world_id=world.world_id,
            created_at=now,
            model="deterministic-npc-chart-only",
            cognition=MingliCognitiveDraft(
                first_look="只读生命树已由确定性四柱生成。",
                whole_chart_thesis=claim,
                salient_phenomena=[],
                hypotheses=[],
                selected_hypothesis_id="",
                work_path=WorkPathReasoning(
                    path_statement="当前暂无已确认主路径。",
                    source=[],
                    transformations=[],
                    target=[],
                    body_function_relation="尚未进入专业路径认知。",
                    closure="uncertain",
                    success_conditions=[],
                    failure_conditions=[],
                    evidence_refs=[evidence_ref],
                    origin="system_enumerated",
                ),
                useful_god_reasoning=[],
                portrait=[],
                prior_predictions=[],
                next_probe=DiscriminatingProbe(
                    probe_id=f"projection-only:{seed.npc_id}",
                    question="当前只观察确定性命盘镜。",
                    purpose="保持 DREAM-PILOT-01 只读边界",
                    distinguishes_hypothesis_refs=[],
                    options=["继续观察"],
                    expected_updates={"继续观察": "unchanged"},
                ),
                unresolved_questions=["专业做功路径尚未形成。"],
                evidence_refs=[evidence_ref],
            ),
            review=EpistemicReviewReceipt(
                passed=True,
                fact_traceability_rate=1.0,
                model="deterministic-npc-chart-only",
                disposition="reliable",
                commit_eligible=True,
                gate_version="deterministic_npc_chart_only.v1",
            ),
            reliability_disposition="reliable",
            reliability_signature=manifest_hash,
        )
        return {
            "case_id": seed.case_id,
            "birth_input": birth.model_dump(mode="json"),
            "world": world.model_dump(mode="json"),
            "record": record.model_dump(mode="json"),
            "life_case": life_case.model_dump(mode="json"),
            "canonical_npc": {
                **manifest,
                "genesis_manifest_hash": manifest_hash,
                "canonical_lifecase_ref": life_case.life_case_id,
                "runtime_capabilities": ["read_only_tree_projection", "onecanvas_mirror"],
                "disabled_capabilities": ["mind_wake", "free_dialogue", "autonomous_action"],
                "professional_path_state": "unavailable_unconfirmed",
                "evidence_boundary": "simulation_identity_not_reality_evidence",
                "created_at": now,
            },
            "status": "active",
            "entry_protocol": "dream_pilot_canonical_npc_bootstrap_v1",
        }


def ensure_authorized_human_projection_life_case(
    *,
    case_store: AgentCaseStore,
    case_id: str,
    user_id: str,
) -> LifeCase:
    """Materialize a chart-only LifeCase after explicit Dream consent.

    Imported cases may predate the formal LifeCase contract. This bridge copies no
    legacy interpretation: it commits only the already-authoritative chart facts so
    CanonicalScene and OneCanvas can remain the sole projection owners.
    """

    row = case_store.get(case_id=case_id, user_id=user_id)
    if row is None or row.get("user_id") != user_id:
        raise ValueError("dream_human_case_not_owned")
    existing = row.get("life_case")
    if isinstance(existing, dict):
        return LifeCase.model_validate(existing)

    world_payload = row.get("world")
    record_payload = row.get("record")
    if not isinstance(world_payload, dict) or not isinstance(record_payload, dict):
        raise ValueError("dream_human_chart_only_source_unavailable")
    world = ChartWorldInstance.model_validate(world_payload)
    record = MingliCognitiveRecord.model_validate(record_payload)
    if record.case_id != case_id or record.world_id != world.world_id:
        raise ValueError("dream_human_chart_only_source_unreliable")

    evidence_ref = next(
        (
            item.fact_id
            for item in world.facts
            if item.kind == "fact" and item.category == "pillars"
        ),
        world.allowed_evidence_refs[0],
    )
    now = datetime.now(timezone.utc).isoformat()
    claim = "这棵树只投影当前用户明确授权的确定性四柱；当前暂无已确认主路径。"
    context_hash = _canonical_hash({
        "case_id": case_id,
        "user_id": user_id,
        "world_id": world.world_id,
        "policy_version": DREAM_PILOT_HUMAN_PROJECTION_POLICY_VERSION,
    })
    overlay = ProfessionalReviewOverlay(
        overlay_id=f"review-dream-human-{context_hash[:20]}",
        cognitive_record_ref=record.record_id,
        review_version="deterministic_human_chart_only.v1",
        assertions_hash=_canonical_hash([]),
        raw_output_hash=_canonical_hash({"claim": claim, "context_hash": context_hash}),
        raw_source_kind="deterministic_system_payload",
        persistence_status="persisted",
        professional_release_status="partially_blocked",
        reviewer="deterministic-dream-consent-bootstrap",
        created_at=now,
    )
    insight = FormalInsight(
        insight_id=f"insight-dream-human-{context_hash[:20]}",
        case_id=case_id,
        case_version="v1",
        type="baseline",
        claim=claim,
        scope={"temporal_scope": "natal", "projection_boundary": "chart_facts_only"},
        basis=InsightBasis(chart_fact_refs=[evidence_ref]),
        reasoning_path=[ReasoningPathStep(
            premise="四柱来自当前档案已经保存的 Canonical ChartWorldInstance。",
            conclusion="本轮只允许生成经授权的只读生命树与同源命盘镜。",
            source_refs=[evidence_ref],
        )],
        conditions=["仅限当前用户明确授权的 DREAM-PILOT-01 封闭只读投影"],
        counter_signals=["旧认知、专业路径和现实人生叙事均不因授权自动晋升"],
        uncertainty=InsightUncertainty(
            level="high",
            reasons=["尚未形成专业路径认知，不得从自然语言或潜在关系猜线。"],
        ),
        provenance=InsightProvenance(
            reasoner_id="deterministic.dream_human_projection",
            reasoner_version=DREAM_PILOT_HUMAN_PROJECTION_POLICY_VERSION,
            theory_version="v50.canonical.chart_facts",
            model_version="none",
            context_hash=context_hash,
            generated_at=now,
            source_record_id=record.record_id,
        ),
        status="reviewed",
        persistence_status="persisted",
        professional_release_status="partially_blocked",
        professional_review_overlay=overlay,
        epistemic_state="reliable",
        source_review_gate="deterministic_human_chart_only.v1",
        projection_payload={
            "identity_class": "authorized_human",
            "professional_path_state": "unavailable_unconfirmed",
        },
    )
    life_case, receipt = commit_baseline_life_case(
        insight=insight,
        world=world,
        profile_id=str(row.get("profile_id") or "") or None,
    )
    if not receipt.passed or life_case.relation_assertions or life_case.path_assertions:
        raise ValueError("dream_human_chart_only_boundary_failed")
    case_store.save(
        case_id=case_id,
        user_id=user_id,
        profile_id=str(row.get("profile_id") or "") or None,
        payload={
            **row,
            "life_case": life_case.model_dump(mode="json"),
            "dream_projection_baseline": {
                "policy_version": DREAM_PILOT_HUMAN_PROJECTION_POLICY_VERSION,
                "source_world_id": world.world_id,
                "source_record_id": record.record_id,
                "projection_boundary": "chart_facts_only",
                "created_at": now,
            },
        },
    )
    return life_case


def _genesis_manifest(seed: CanonicalNpcSeed) -> dict[str, Any]:
    return {
        "schema_version": "deepbazi.canonical_npc_genesis.v1",
        "npc_id": seed.npc_id,
        "canonical_identity_ref": f"canonical-npc:{seed.npc_id}",
        "identity_class": "canonical_npc",
        "origin_mode": "world_genesis_import",
        "display_name": seed.display_name,
        "not_human": True,
        "not_reality_evidence": True,
        "birth_facts": {
            "gender": seed.gender,
            "calendar_type": "solar",
            "birth_date": seed.birth_date,
            "birth_time": seed.birth_time,
            "birth_location": seed.birth_location,
            "timezone": seed.timezone,
        },
        "policy_version": DREAM_PILOT_NPC_POLICY_VERSION,
    }


def _validate_existing_npc(
    *,
    row: dict[str, Any],
    seed: CanonicalNpcSeed,
    manifest_hash: str,
) -> None:
    npc = row.get("canonical_npc") if isinstance(row.get("canonical_npc"), dict) else {}
    if (
        npc.get("npc_id") != seed.npc_id
        or npc.get("identity_class") != "canonical_npc"
        or npc.get("not_human") is not True
        or npc.get("not_reality_evidence") is not True
        or npc.get("genesis_manifest_hash") != manifest_hash
    ):
        raise ValueError(f"canonical_npc_identity_conflict:{seed.npc_id}")


def _npc_grant_identity(npc_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"dream-pilot-npc|{npc_id}".encode()).hexdigest()
    return f"dream-npc-grant-{digest[:24]}", f"dream-scene-npc-{digest[:32]}"


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


__all__ = [
    "CANONICAL_NPC_IDS",
    "CANONICAL_NPC_SEEDS",
    "CanonicalNpcBootstrapResult",
    "DreamCanonicalNpcBootstrapService",
    "ensure_authorized_human_projection_life_case",
]
