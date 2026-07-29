from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from abu_v60.knowledge import BaziFoundationProfile


@dataclass(frozen=True, slots=True)
class FoundationRuntimeMaps:
    """Executable maps derived from one exact admitted Foundation Profile."""

    profile_id: str
    profile_version: str
    profile_hash: str
    profile_source_ref: str
    stem_elements: Mapping[str, str]
    stem_polarity: Mapping[str, str]
    hidden_stems: Mapping[str, tuple[str, ...]]
    six_clash: frozenset[frozenset[str]]
    six_harmony: frozenset[frozenset[str]]
    forbidden_inferences: tuple[str, ...]

    @classmethod
    def from_profile(
        cls,
        profile: BaziFoundationProfile,
    ) -> FoundationRuntimeMaps:
        return cls(
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_hash=profile.profile_hash,
            profile_source_ref=profile.source_ref,
            stem_elements=MappingProxyType({item.stem: item.element for item in profile.stems}),
            stem_polarity=MappingProxyType({item.stem: item.polarity for item in profile.stems}),
            hidden_stems=MappingProxyType(
                {item.branch: item.hidden_stems for item in profile.branches}
            ),
            six_clash=frozenset(
                frozenset((item.left_branch, item.right_branch))
                for item in profile.relations
                if item.relation_type == "six_clash_membership"
            ),
            six_harmony=frozenset(
                frozenset((item.left_branch, item.right_branch))
                for item in profile.relations
                if item.relation_type == "six_harmony_membership"
            ),
            forbidden_inferences=profile.forbidden_inferences,
        )
