from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Literal

from abu_v60.mingli.quant_contracts import (
    MingliQuantFoundationVector,
    SourceManifestationEvidence,
)
from abu_v60.mingli.source_review_contracts import (
    MingliSourceCoordinateReviewVector,
    SourceCoordinateReviewEvidence,
)
from abu_v60.mingli.source_usability_contracts import (
    PILLAR_SLOT_ORDER,
    MingliSourceUsabilityPrerequisiteEnvelope,
    SourceCarrierUsabilityPrerequisite,
    SourceUsabilityRequirement,
    SourceUsabilityResearchScope,
)
from abu_v60.provenance import stable_ref

SourceScopeId = Literal[
    "EXACT_IDENTITY_ONLY",
    "ELEMENT_AFFINITY_INCLUDED",
]


class MingliSourceUsabilityPrerequisiteProjector:
    """Expose competing source scopes and six bounded verification conditions."""

    def project(
        self,
        *,
        quant_vector: MingliQuantFoundationVector,
        source_review_vector: MingliSourceCoordinateReviewVector,
    ) -> MingliSourceUsabilityPrerequisiteEnvelope:
        self._validate_lineage(
            quant_vector=quant_vector,
            source_review_vector=source_review_vector,
        )
        reviews_by_source = {
            item.source_evidence_ref: item for item in source_review_vector.reviews
        }
        groups: dict[
            tuple[str, str],
            list[tuple[SourceManifestationEvidence, SourceCoordinateReviewEvidence]],
        ] = defaultdict(list)
        for source in quant_vector.source_manifestation_evidence:
            groups[(source.visible_slot, source.visible_stem)].append(
                (source, reviews_by_source[source.evidence_ref])
            )
        carriers = tuple(
            self._carrier(items=tuple(groups[key]))
            for key in sorted(
                groups,
                key=lambda item: (PILLAR_SLOT_ORDER.index(item[0]), item[1]),
            )
        )
        strict_scopes = tuple(item.scopes[0] for item in carriers)
        inclusive_scopes = tuple(item.scopes[1] for item in carriers)
        return MingliSourceUsabilityPrerequisiteEnvelope.issue(
            case_ref=quant_vector.case_ref,
            chart_version_ref=quant_vector.chart_version_ref,
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            source_review_vector_ref=source_review_vector.vector_ref,
            source_review_vector_hash=source_review_vector.vector_hash,
            carriers=carriers,
            carrier_count=len(carriers),
            exact_identity_only_clear_count=sum(item.clear_count for item in strict_scopes),
            exact_identity_only_review_required_count=sum(
                item.relation_review_count for item in strict_scopes
            ),
            element_affinity_included_clear_count=sum(
                item.clear_count for item in inclusive_scopes
            ),
            element_affinity_included_review_required_count=sum(
                item.relation_review_count for item in inclusive_scopes
            ),
            competing_carrier_count=sum(
                strict.source_review_refs != inclusive.source_review_refs
                for strict, inclusive in zip(
                    strict_scopes,
                    inclusive_scopes,
                    strict=True,
                )
            ),
            ready_carrier_count=0,
        )

    @staticmethod
    def _validate_lineage(
        *,
        quant_vector: MingliQuantFoundationVector,
        source_review_vector: MingliSourceCoordinateReviewVector,
    ) -> None:
        if (
            source_review_vector.case_ref != quant_vector.case_ref
            or source_review_vector.chart_version_ref != quant_vector.chart_version_ref
        ):
            raise ValueError("source_usability_case_chart_lineage_mismatch")
        if (
            source_review_vector.quant_vector_ref != quant_vector.vector_ref
            or source_review_vector.quant_vector_hash != quant_vector.vector_hash
        ):
            raise ValueError("source_usability_quant_vector_lineage_mismatch")
        sources = {item.evidence_ref: item for item in quant_vector.source_manifestation_evidence}
        reviews = {item.source_evidence_ref: item for item in source_review_vector.reviews}
        if len(sources) != len(quant_vector.source_manifestation_evidence):
            raise ValueError("source_usability_quant_source_identity_not_unique")
        if len(reviews) != len(source_review_vector.reviews):
            raise ValueError("source_usability_review_source_identity_not_unique")
        if set(sources) != set(reviews):
            raise ValueError("source_usability_source_review_bijection_mismatch")
        for source_ref, source in sources.items():
            review = reviews[source_ref]
            if (
                review.visible_slot != source.visible_slot
                or review.visible_stem != source.visible_stem
                or review.source_slot != source.source_slot
                or review.source_branch != source.source_branch
                or review.hidden_stem != source.hidden_stem
                or review.source_match_kind != source.source_match_kind
            ):
                raise ValueError("source_usability_source_review_coordinate_mismatch")

    def _carrier(
        self,
        *,
        items: Sequence[tuple[SourceManifestationEvidence, SourceCoordinateReviewEvidence]],
    ) -> SourceCarrierUsabilityPrerequisite:
        visible_slot = items[0][0].visible_slot
        visible_stem = items[0][0].visible_stem
        strict_items = tuple(
            item for item in items if item[0].source_match_kind == "EXACT_IDENTITY"
        )
        inclusive_items = tuple(items)
        scopes = (
            self._scope(
                visible_slot=visible_slot,
                visible_stem=visible_stem,
                scope_id="EXACT_IDENTITY_ONLY",
                items=strict_items,
            ),
            self._scope(
                visible_slot=visible_slot,
                visible_stem=visible_stem,
                scope_id="ELEMENT_AFFINITY_INCLUDED",
                items=inclusive_items,
            ),
        )
        return SourceCarrierUsabilityPrerequisite.issue(
            visible_slot=visible_slot,
            visible_stem=visible_stem,
            scopes=scopes,
            requirements=self._requirements(inclusive_scope=scopes[1]),
        )

    @staticmethod
    def _scope(
        *,
        visible_slot: str,
        visible_stem: str,
        scope_id: SourceScopeId,
        items: Sequence[tuple[SourceManifestationEvidence, SourceCoordinateReviewEvidence]],
    ) -> SourceUsabilityResearchScope:
        source_review_refs = tuple(sorted(item[1].review_ref for item in items))
        relation_review_refs = tuple(
            sorted(item[1].review_ref for item in items if item[1].relation_intersections)
        )
        intersection_refs = tuple(
            sorted(
                relation.intersection_ref
                for _, review in items
                for relation in review.relation_intersections
            )
        )
        identity = {
            "visible_slot": visible_slot,
            "visible_stem": visible_stem,
            "scope_id": scope_id,
            "source_review_refs": source_review_refs,
            "relation_review_refs": relation_review_refs,
            "intersection_refs": intersection_refs,
        }
        return SourceUsabilityResearchScope(
            scope_ref=stable_ref("v60-source-usability-scope", identity),
            scope_id=scope_id,
            source_review_refs=source_review_refs,
            relation_review_refs=relation_review_refs,
            intersection_refs=intersection_refs,
            source_review_count=len(source_review_refs),
            clear_count=len(source_review_refs) - len(relation_review_refs),
            relation_review_count=len(relation_review_refs),
            intersection_count=len(intersection_refs),
            relation_effect_status="UNRESOLVED",
            root_usability_status="UNRESOLVED",
            selection_authority=False,
        )

    @staticmethod
    def _requirements(
        *,
        inclusive_scope: SourceUsabilityResearchScope,
    ) -> tuple[SourceUsabilityRequirement, ...]:
        relation_triggered = bool(inclusive_scope.relation_review_refs)
        multiple_sources = inclusive_scope.source_review_count > 1
        return (
            SourceUsabilityRequirement(
                requirement_id="MATCH_SCOPE_RULE",
                status="NOT_ADMITTED",
                evidence_refs=inclusive_scope.source_review_refs,
                meaning=(
                    "同干与同五行异干两种候选范围都可追溯，"
                    "但当前没有规则决定哪一种可进入来源可用性讨论。"
                ),
                next_evidence="有来源、可复核的来源匹配范围与适用边界规则。",
            ),
            SourceUsabilityRequirement(
                requirement_id="RELATION_EFFECT_RULE",
                status=("NOT_ADMITTED" if relation_triggered else "NOT_TRIGGERED"),
                evidence_refs=inclusive_scope.intersection_refs,
                meaning=(
                    "已有关系成员事实命中来源坐标，但没有作用方向、完成条件或阻断条件。"
                    if relation_triggered
                    else "本版已准入的六冲、六合没有命中这些来源坐标；这不是来源可用的正向证据。"
                ),
                next_evidence=(
                    "精确到该关系配置的作用规则、上下文要求与反证。"
                    if relation_triggered
                    else "若后续出现关系触发，再按配置补作用规则；当前继续核查其他门槛。"
                ),
            ),
            SourceUsabilityRequirement(
                requirement_id="SEASONAL_CAPACITY_RULE",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="当前没有把月令、根透与承载条件合成为容量证据。",
                next_evidence="版本化季节容量规则及其所需的原始坐标证据。",
            ),
            SourceUsabilityRequirement(
                requirement_id="MULTI_SOURCE_AGGREGATION_RULE",
                status=("NOT_ADMITTED" if multiple_sources else "NOT_TRIGGERED"),
                evidence_refs=(inclusive_scope.source_review_refs if multiple_sources else ()),
                meaning=(
                    "同一明干有多个来源候选，当前不能用任一清晰或任一命中自动代表整个载体。"
                    if multiple_sources
                    else "该载体当前只有一个来源候选，不触发多来源聚合问题。"
                ),
                next_evidence=(
                    "多个来源并存时的合并、冲突与撤销规则。"
                    if multiple_sources
                    else "若来源候选增加，再补多来源聚合规则。"
                ),
            ),
            SourceUsabilityRequirement(
                requirement_id="ROOT_USABILITY_RULE",
                status="NOT_ADMITTED",
                evidence_refs=inclusive_scope.source_review_refs,
                meaning="来源坐标存在不等于已经证明来源可用。",
                next_evidence="同时约束匹配范围、关系处置与容量条件的可用性规则。",
            ),
            SourceUsabilityRequirement(
                requirement_id="PROFESSIONAL_ADMISSION",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="当前投影只允许整理问题，不具有专业结论权限。",
                next_evidence="Owner 专业审阅通过的规则版本、来源与适用边界。",
            ),
        )
