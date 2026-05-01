from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.features.schema import FeatureLayer


@dataclass(frozen=True)
class EvidencePack:
    version: str
    feature_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    boundaries: tuple[str, ...]
    measurement_domains: tuple[str, ...] = ()
    guardrails: tuple[str, ...] = (
        "EVIDENCE_PACK_CONTEXT_ONLY",
        "NO_UNSUPPORTED_CLAIM",
        "NO_ANSWER_MUTATION",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evidence_pack(feature_layer: FeatureLayer) -> EvidencePack:
    refs: list[str] = []
    boundaries: list[str] = []
    for feature in feature_layer.features:
        refs.extend(ref.ref_id for ref in feature.evidence_refs)
        boundaries.append(feature.boundary)
    return EvidencePack(
        version="v20.evidence_pack.v1",
        feature_ids=tuple(feature.feature_id for feature in feature_layer.features),
        evidence_refs=tuple(dict.fromkeys(refs)),
        boundaries=tuple(dict.fromkeys(boundaries)),
        measurement_domains=tuple(dict.fromkeys(feature.domain for feature in feature_layer.features)),
    )
