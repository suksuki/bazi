from __future__ import annotations

from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.relation_effect_admission import (
    MingliRelationEffectAdmissionProjector,
)
from abu_v60.mingli.relation_effect_evidence import (
    MingliRelationEffectEvidencePacketProjector,
)
from abu_v60.mingli.relation_effect_evidence_contracts import (
    MingliRelationEffectEvidencePacketEnvelope,
)
from abu_v60.mingli.relation_effect_frontier import (
    MingliRelationEffectResearchFrontierProjector,
)
from abu_v60.mingli.source_discussion import (
    MingliSourceDiscussionAbstentionProjector,
)
from abu_v60.mingli.source_review_store import MingliSourceReviewVectorStore
from abu_v60.mingli.source_usability import (
    MingliSourceUsabilityPrerequisiteProjector,
)


class MingliRelationEffectHistoricalPacketError(ValueError):
    pass


class MingliRelationEffectHistoricalPacketResolver:
    """Rebuild one packet from its immutable historical Reading lineage."""

    def __init__(
        self,
        engine: Engine,
        *,
        readings: MingliReadingStore | None = None,
        quant_vectors: MingliQuantVectorStore | None = None,
        source_review_vectors: MingliSourceReviewVectorStore | None = None,
        source_usability: (
            MingliSourceUsabilityPrerequisiteProjector | None
        ) = None,
        source_discussion: (
            MingliSourceDiscussionAbstentionProjector | None
        ) = None,
        frontier: (
            MingliRelationEffectResearchFrontierProjector | None
        ) = None,
        admission: MingliRelationEffectAdmissionProjector | None = None,
        evidence: MingliRelationEffectEvidencePacketProjector | None = None,
    ) -> None:
        self._engine = engine
        self._readings = readings or MingliReadingStore(engine)
        self._quant_vectors = quant_vectors or MingliQuantVectorStore(engine)
        self._source_review_vectors = (
            source_review_vectors or MingliSourceReviewVectorStore(engine)
        )
        self._source_usability = (
            source_usability or MingliSourceUsabilityPrerequisiteProjector()
        )
        self._source_discussion = (
            source_discussion or MingliSourceDiscussionAbstentionProjector()
        )
        self._frontier = (
            frontier or MingliRelationEffectResearchFrontierProjector()
        )
        self._admission = (
            admission or MingliRelationEffectAdmissionProjector()
        )
        self._evidence = (
            evidence or MingliRelationEffectEvidencePacketProjector()
        )

    def resolve(
        self,
        *,
        reading_ref: str,
    ) -> MingliRelationEffectEvidencePacketEnvelope:
        with self._engine.connect() as connection:
            return self.resolve_in_connection(
                connection,
                reading_ref=reading_ref,
            )

    def resolve_in_connection(
        self,
        connection: Connection,
        *,
        reading_ref: str,
    ) -> MingliRelationEffectEvidencePacketEnvelope:
        reading = self._readings.get_in_connection(
            connection,
            reading_ref=reading_ref,
        )
        if (
            reading.quant_vector_ref is None
            or reading.quant_vector_hash is None
            or reading.source_review_vector_ref is None
            or reading.source_review_vector_hash is None
        ):
            raise MingliRelationEffectHistoricalPacketError(
                "relation_effect_historical_packet_vector_lineage_missing"
            )
        quant_vector = self._quant_vectors.get_in_connection(
            connection,
            vector_ref=reading.quant_vector_ref,
        )
        source_review_vector = (
            self._source_review_vectors.get_in_connection(
                connection,
                vector_ref=reading.source_review_vector_ref,
            )
        )
        if (
            quant_vector.vector_ref,
            quant_vector.vector_hash,
            source_review_vector.vector_ref,
            source_review_vector.vector_hash,
        ) != (
            reading.quant_vector_ref,
            reading.quant_vector_hash,
            reading.source_review_vector_ref,
            reading.source_review_vector_hash,
        ):
            raise MingliRelationEffectHistoricalPacketError(
                "relation_effect_historical_packet_vector_lineage_mismatch"
            )

        prerequisite = self._source_usability.project(
            quant_vector=quant_vector,
            source_review_vector=source_review_vector,
        )
        refusal = self._source_discussion.project(
            reading=reading,
            prerequisite=prerequisite,
        )
        frontier = self._frontier.project(
            reading=reading,
            source_review_vector=source_review_vector,
            prerequisite=prerequisite,
            refusal=refusal,
        )
        admission_review = self._admission.project(frontier=frontier)
        return self._evidence.project(
            reading=reading,
            frontier=frontier,
            admission_review=admission_review,
        )
