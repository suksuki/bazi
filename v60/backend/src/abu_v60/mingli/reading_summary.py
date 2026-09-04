from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_contracts import MingliAgentReadingEnvelope
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.agent_runtime import mingli_agent_runtime_manifest
from abu_v60.mingli.agent_store import MingliAgentReadingStore
from abu_v60.mingli.brief import MingliReadingBriefProjector
from abu_v60.mingli.domain_store import MingliLifeDomainVectorStore
from abu_v60.mingli.focused_pass_store import MingliFocusedPassStore
from abu_v60.mingli.focused_reading_contracts import (
    MINGLI_FOCUS_ORDER,
    MingliFocusedPassRecord,
    MingliFocusedReadingEnvelope,
)
from abu_v60.mingli.focused_reading_runtime import (
    mingli_focused_runtime_manifest,
)
from abu_v60.mingli.focused_reading_store import MingliFocusedReadingStore
from abu_v60.mingli.mechanism_decision import MingliMechanismComparisonService
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_claim_graph import MingliReadingClaimGraphProjector
from abu_v60.mingli.reading_claim_graph_contracts import MingliReadingClaimGraph
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.service import CaseNotFoundError, MingliCaseService
from abu_v60.mingli.showcases import SHOWCASE_ACCOUNT_REF, SHOWCASE_BY_SUBJECT
from abu_v60.mingli.timing_store import MingliTimingVectorStore
from abu_v60.provenance import content_hash, stable_ref

MINGLI_READING_SUMMARY_VERSION = "v60.mingli-reading-summary.008"
SUPPORTED_SUBJECT_KINDS = frozenset({"HUMAN_OWNER", "HUMAN_REFERENCE", "CANONICAL_SYNTHETIC"})
SHOWCASE_CASE_REFS = frozenset(item.case_ref for item in SHOWCASE_BY_SUBJECT.values())


class MingliReadingSummaryError(ValueError):
    pass


class MingliReadingSummaryProjection(BaseModel):
    """A private four-layer view binding facts and one optional Agent reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary_ref: str = Field(min_length=1)
    summary_hash: str = Field(min_length=64, max_length=64)
    summary_version: Literal["v60.mingli-reading-summary.008"]
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    subject_kind: Literal[
        "HUMAN_OWNER",
        "HUMAN_REFERENCE",
        "CANONICAL_SYNTHETIC",
    ]
    reading_brief: dict[str, Any]
    focused_runtime_status: Literal["READY_FOR_OWNER_REVIEW", "DISABLED"]
    focused_generation_available: bool
    focused_status: Literal["READY", "PARTIAL", "NOT_GENERATED"]
    focused_reading: MingliFocusedReadingEnvelope | None
    focused_pass_records: tuple[MingliFocusedPassRecord, ...] = Field(max_length=5)
    focused_projection_scope: Literal["OWNER_REVIEW", "NOT_GENERATED"]
    agent_runtime_status: Literal[
        "READY",
        "DISABLED",
        "MISCONFIGURED",
        "READY_FOR_OWNER_REVIEW",
    ]
    agent_generation_available: bool
    agent_status: Literal["READY", "NOT_GENERATED"]
    agent_reading: MingliAgentReadingEnvelope | None
    claim_graph: MingliReadingClaimGraph | None
    agent_projection_scope: Literal["OWNER_REVIEW", "PUBLIC", "NOT_GENERATED"]
    image_projection_status: Literal["AGENT_INTERPRETATION", "NOT_GENERATED"]
    professional_verdict_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliReadingSummaryProjection:
        identity = self.model_dump(
            mode="json",
            exclude={"summary_ref", "summary_hash"},
        )
        if self.summary_hash != content_hash(identity):
            raise ValueError("mingli_reading_summary_hash_mismatch")
        if self.summary_ref != stable_ref("v60-mingli-reading-summary", identity):
            raise ValueError("mingli_reading_summary_ref_mismatch")
        lineage = self.reading_brief.get("lineage")
        if not isinstance(lineage, dict) or (
            lineage.get("reading_ref"),
            lineage.get("reading_hash"),
        ) != (self.reading_ref, self.reading_hash):
            raise ValueError("mingli_reading_summary_brief_lineage_mismatch")
        if self.agent_reading is None:
            if (
                self.agent_status != "NOT_GENERATED"
                or self.claim_graph is not None
                or self.agent_projection_scope != "NOT_GENERATED"
            ):
                raise ValueError("mingli_reading_summary_agent_status_mismatch")
        elif (
            self.agent_status != "READY"
            or self.claim_graph is None
            or self.agent_projection_scope not in {"OWNER_REVIEW", "PUBLIC"}
            or self.agent_reading.case_ref != self.case_ref
            or self.agent_reading.chart_version_ref != self.chart_version_ref
            or self.agent_reading.life_case_revision_ref != self.life_case_revision_ref
            or self.agent_reading.reading_ref != self.reading_ref
            or self.agent_reading.reading_hash != self.reading_hash
        ):
            raise ValueError("mingli_reading_summary_agent_lineage_mismatch")
        if self.claim_graph is not None and (
            self.claim_graph.case_ref != self.case_ref
            or self.claim_graph.chart_version_ref != self.chart_version_ref
            or self.claim_graph.life_case_revision_ref != self.life_case_revision_ref
            or self.claim_graph.reading_ref != self.reading_ref
            or self.claim_graph.reading_hash != self.reading_hash
            or self.agent_reading is None
            or self.claim_graph.agent_reading_ref != self.agent_reading.agent_reading_ref
            or self.claim_graph.agent_reading_hash != self.agent_reading.agent_reading_hash
        ):
            raise ValueError("mingli_reading_summary_claim_graph_lineage_mismatch")
        if (
            self.claim_graph is not None
            and not self.claim_graph.public_projection_allowed
            and self.agent_projection_scope != "OWNER_REVIEW"
        ):
            raise ValueError("mingli_reading_summary_claim_graph_scope_mismatch")
        if self.agent_generation_available != (
            self.agent_runtime_status in {"READY", "READY_FOR_OWNER_REVIEW"}
        ):
            raise ValueError("mingli_reading_summary_agent_runtime_status_mismatch")
        records = self.focused_pass_records
        record_focuses = tuple(item.focus for item in records)
        if record_focuses != tuple(
            focus for focus in MINGLI_FOCUS_ORDER if focus in record_focuses
        ):
            raise ValueError("mingli_reading_summary_focused_pass_order_invalid")
        if any(
            item.case_ref != self.case_ref
            or item.chart_version_ref != self.chart_version_ref
            or item.life_case_revision_ref != self.life_case_revision_ref
            or item.reading_ref != self.reading_ref
            or item.reading_hash != self.reading_hash
            for item in records
        ):
            raise ValueError("mingli_reading_summary_focused_pass_lineage_mismatch")
        structure = next(
            (item for item in records if item.focus == "STRUCTURE"),
            None,
        )
        if any(
            item.focus != "STRUCTURE"
            and (structure is None or item.structure_pass_hash != structure.pass_result.pass_hash)
            for item in records
        ):
            raise ValueError("mingli_reading_summary_focused_structure_mismatch")
        has_focused = self.focused_reading is not None or bool(records)
        expected_focused_status = (
            "READY"
            if self.focused_reading is not None or len(records) == len(MINGLI_FOCUS_ORDER)
            else "PARTIAL"
            if records
            else "NOT_GENERATED"
        )
        expected_focused_scope = "OWNER_REVIEW" if has_focused else "NOT_GENERATED"
        if (
            self.focused_status != expected_focused_status
            or self.focused_projection_scope != expected_focused_scope
        ):
            raise ValueError("mingli_reading_summary_focused_status_mismatch")
        if self.focused_reading is not None and (
            self.focused_reading.case_ref != self.case_ref
            or self.focused_reading.chart_version_ref != self.chart_version_ref
            or self.focused_reading.life_case_revision_ref != self.life_case_revision_ref
            or self.focused_reading.reading_ref != self.reading_ref
            or self.focused_reading.reading_hash != self.reading_hash
        ):
            raise ValueError("mingli_reading_summary_focused_lineage_mismatch")
        if self.focused_generation_available != (
            self.focused_runtime_status == "READY_FOR_OWNER_REVIEW"
        ):
            raise ValueError("mingli_reading_summary_focused_runtime_status_mismatch")
        expected_image_status = (
            "AGENT_INTERPRETATION"
            if has_focused or self.agent_reading is not None
            else "NOT_GENERATED"
        )
        if self.image_projection_status != expected_image_status:
            raise ValueError("mingli_reading_summary_image_status_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliReadingSummaryProjection:
        agent_reading = values.get("agent_reading")
        focused_reading = values.get("focused_reading")
        focused_pass_records = tuple(values.get("focused_pass_records", ()))
        claim_graph = values.get("claim_graph")
        if (agent_reading is None) != (claim_graph is None):
            raise ValueError("mingli_reading_summary_claim_graph_copresence_required")
        publication_allowed = bool(values.pop("publication_allowed", False))
        if (
            publication_allowed
            and isinstance(claim_graph, MingliReadingClaimGraph)
            and not claim_graph.public_projection_allowed
        ):
            raise ValueError("mingli_reading_summary_unqualified_graph_cannot_be_public")
        normalized_values = {
            **values,
            "agent_reading": (
                agent_reading.model_dump(mode="json")
                if isinstance(agent_reading, BaseModel)
                else agent_reading
            ),
            "focused_reading": (
                focused_reading.model_dump(mode="json")
                if isinstance(focused_reading, BaseModel)
                else focused_reading
            ),
            "focused_pass_records": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in focused_pass_records
            ),
            "claim_graph": (
                claim_graph.model_dump(mode="json")
                if isinstance(claim_graph, BaseModel)
                else claim_graph
            ),
        }
        identity = {
            **normalized_values,
            "summary_version": MINGLI_READING_SUMMARY_VERSION,
            "focused_status": (
                "READY"
                if focused_reading is not None
                or len(focused_pass_records) == len(MINGLI_FOCUS_ORDER)
                else "PARTIAL"
                if focused_pass_records
                else "NOT_GENERATED"
            ),
            "focused_projection_scope": (
                "OWNER_REVIEW"
                if focused_reading is not None or focused_pass_records
                else "NOT_GENERATED"
            ),
            "agent_status": "READY" if agent_reading is not None else "NOT_GENERATED",
            "agent_projection_scope": (
                "PUBLIC"
                if agent_reading is not None and publication_allowed
                else "OWNER_REVIEW"
                if agent_reading is not None
                else "NOT_GENERATED"
            ),
            "image_projection_status": (
                "AGENT_INTERPRETATION"
                if focused_reading is not None or focused_pass_records or agent_reading is not None
                else "NOT_GENERATED"
            ),
            "professional_verdict_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            summary_ref=stable_ref("v60-mingli-reading-summary", identity),
            summary_hash=content_hash(identity),
            **identity,
        )


class MingliReadingSummaryService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._cases = MingliCaseService(engine)
        self._readings = MingliReadingStore(engine)
        self._agent_readings = MingliAgentReadingStore(engine)
        self._agent_runtime_manifest = mingli_agent_runtime_manifest()
        self._agent_runtime_profile = self._agent_runtime_manifest["profile"]
        self._focused_readings = MingliFocusedReadingStore(engine)
        self._focused_passes = MingliFocusedPassStore(engine)
        self._focused_runtime_manifest = mingli_focused_runtime_manifest()
        self._quant = MingliQuantVectorStore(engine)
        self._mechanism = MingliMechanismVectorStore(engine)
        self._timing = MingliTimingVectorStore(engine)
        self._domains = MingliLifeDomainVectorStore(engine)
        self._comparisons = MingliMechanismComparisonService(engine)
        self._brief = MingliReadingBriefProjector()
        self._claim_graph = MingliReadingClaimGraphProjector()
        self._agent_packet = MingliAgentCasePacketCompiler()

    def project(
        self,
        *,
        account_ref: str,
        case_ref: str,
    ) -> MingliReadingSummaryProjection:
        try:
            workspace = self._cases.workspace(
                account_ref=(
                    SHOWCASE_ACCOUNT_REF if case_ref in SHOWCASE_CASE_REFS else account_ref
                ),
                case_ref=case_ref,
            )
        except CaseNotFoundError as exc:
            raise MingliReadingSummaryError("mingli_reading_summary_case_not_found") from exc
        subject_kind = str(workspace["case"]["subject_kind"])
        if subject_kind not in SUPPORTED_SUBJECT_KINDS:
            raise MingliReadingSummaryError("mingli_reading_summary_subject_kind_unsupported")

        chart_ref = str(workspace["chart"]["chart_version_ref"])
        life_case_ref = str(workspace["life_case"]["life_case_revision_ref"])
        with self._engine.connect() as connection:
            reading_ref = connection.execute(
                text(
                    """
                    SELECT reading_ref
                    FROM mingli.readings
                    WHERE case_ref = :case_ref
                      AND chart_version_ref = :chart_version_ref
                      AND life_case_revision_ref = :life_case_revision_ref
                    ORDER BY created_at DESC, reading_ref DESC
                    LIMIT 1
                    """
                ),
                {
                    "case_ref": case_ref,
                    "chart_version_ref": chart_ref,
                    "life_case_revision_ref": life_case_ref,
                },
            ).scalar_one_or_none()
        if reading_ref is None:
            raise MingliReadingSummaryError("mingli_reading_summary_not_materialized")

        reading = self._readings.get(reading_ref=str(reading_ref))
        quant = self._quant.get(vector_ref=str(reading.quant_vector_ref))
        mechanism = self._mechanism.get(vector_ref=str(reading.mechanism_vector_ref))
        timing = self._timing.get(vector_ref=str(reading.timing_vector_ref))
        domains = self._domains.get(vector_ref=str(reading.life_domain_vector_ref))
        if not (
            reading.case_ref == case_ref
            and reading.chart_version_ref == chart_ref
            and reading.life_case_revision_ref == life_case_ref
            and quant.case_ref == case_ref
            and quant.chart_version_ref == chart_ref
            and mechanism.case_ref == case_ref
            and mechanism.chart_version_ref == chart_ref
            and timing.case_ref == case_ref
            and timing.chart_version_ref == chart_ref
            and timing.life_case_revision_ref == life_case_ref
            and domains.case_ref == case_ref
            and domains.chart_version_ref == chart_ref
            and domains.life_case_revision_ref == life_case_ref
            and domains.mechanism_vector_ref == mechanism.vector_ref
            and domains.timing_vector_ref == timing.vector_ref
        ):
            raise MingliReadingSummaryError("mingli_reading_summary_lineage_conflict")

        comparison = self._comparisons.current_state(vector=mechanism)
        brief = self._brief.project(
            reading=reading,
            pillars=workspace["chart"]["pillars"],
            fact_count=len(workspace["facts"]),
            quant_vector=quant,
            mechanism_vector=mechanism,
            timing_vector=timing,
            life_domain_vector=domains,
            mechanism_comparison=comparison,
        )
        agent_reading = None
        if (
            self._agent_runtime_manifest["publication_allowed"] is True
            or self._agent_runtime_manifest["owner_review_allowed"] is True
        ):
            agent_reading = self._agent_readings.latest(
                requester_account_ref=account_ref,
                case_ref=case_ref,
                reading_ref=reading.reading_ref,
                reading_hash=reading.reading_hash,
                agent_profile_ref=str(self._agent_runtime_profile["agent_profile_ref"]),
                agent_profile_hash=str(self._agent_runtime_profile["agent_profile_hash"]),
                provider_profile_ref=str(self._agent_runtime_profile["provider_profile_ref"]),
                provider_profile_hash=str(self._agent_runtime_profile["provider_profile_hash"]),
                prompt_ref=str(self._agent_runtime_profile["prompt_ref"]),
                prompt_hash=str(self._agent_runtime_profile["prompt_hash"]),
            )
        focused_reading = None
        focused_pass_records: tuple[MingliFocusedPassRecord, ...] = ()
        focused_profile = self._focused_runtime_manifest.get("provider_profile")
        if isinstance(focused_profile, dict):
            focused_reading = self._focused_readings.latest(
                requester_account_ref=account_ref,
                case_ref=case_ref,
                reading_ref=reading.reading_ref,
                reading_hash=reading.reading_hash,
                provider_profile_hash=str(self._focused_runtime_manifest["provider_profile_hash"]),
                prompt_hash=str(self._focused_runtime_manifest["prompt_hash"]),
            )
            focused_pass_records = self._focused_passes.latest_all(
                requester_account_ref=account_ref,
                case_ref=case_ref,
                reading_ref=reading.reading_ref,
                reading_hash=reading.reading_hash,
                provider_profile_hash=str(self._focused_runtime_manifest["provider_profile_hash"]),
                prompt_hash=str(self._focused_runtime_manifest["prompt_hash"]),
            )
        claim_graph = None
        if agent_reading is not None:
            packet = self._agent_packet.compile(
                workspace=workspace,
                reading=reading,
                quant_vector=quant,
                mechanism_vector=mechanism,
                timing_vector=timing,
            )
            claim_graph = self._claim_graph.project(
                agent_reading,
                packet=packet,
            )
        return MingliReadingSummaryProjection.issue(
            case_ref=case_ref,
            chart_version_ref=chart_ref,
            life_case_revision_ref=life_case_ref,
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            subject_kind=subject_kind,
            reading_brief=brief,
            focused_runtime_status=str(self._focused_runtime_manifest["status"]),
            focused_generation_available=(
                self._focused_runtime_manifest["status"] == "READY_FOR_OWNER_REVIEW"
            ),
            focused_reading=focused_reading,
            focused_pass_records=focused_pass_records,
            agent_runtime_status=str(self._agent_runtime_manifest["status"]),
            agent_generation_available=(
                self._agent_runtime_manifest["status"] in {"READY", "READY_FOR_OWNER_REVIEW"}
            ),
            agent_reading=agent_reading,
            claim_graph=claim_graph,
            publication_allowed=bool(self._agent_runtime_manifest["publication_allowed"]),
        )
