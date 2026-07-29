from __future__ import annotations

from collections.abc import Mapping
from typing import Any

MINGLI_READING_VERSION = "v60.mingli-reading.006"
LIFE_DOMAIN_MINGLI_READING_VERSION = "v60.mingli-reading.005"
TIMING_MINGLI_READING_VERSION = "v60.mingli-reading.004"
MECHANISM_MINGLI_READING_VERSION = "v60.mingli-reading.003"
QUANT_MINGLI_READING_VERSION = "v60.mingli-reading.002"
LEGACY_MINGLI_READING_VERSION = "v60.mingli-reading.001"

SOURCE_REVIEW_FIELDS = {
    "source_review_profile",
    "source_review_vector_ref",
    "source_review_vector_hash",
}
DOMAIN_FIELDS = {
    "life_domain_vector_ref",
    "life_domain_vector_hash",
}
TIMING_FIELDS = {
    "timing_evidence_profile",
    "timing_vector_ref",
    "timing_vector_hash",
}
MECHANISM_FIELDS = {
    "mechanism_evidence_profile",
    "mechanism_vector_ref",
    "mechanism_vector_hash",
}
QUANT_FIELDS = {
    "quant_foundation_profile",
    "quant_vector_ref",
    "quant_vector_hash",
}


def validate_reading_optional_fields(
    *,
    reading_version: str,
    values: Mapping[str, Any],
) -> None:
    groups = {
        "source_review": tuple(values[key] for key in SOURCE_REVIEW_FIELDS),
        "domain": tuple(values[key] for key in DOMAIN_FIELDS),
        "timing": tuple(values[key] for key in TIMING_FIELDS),
        "mechanism": tuple(values[key] for key in MECHANISM_FIELDS),
        "quant": tuple(values[key] for key in QUANT_FIELDS),
    }
    if reading_version == MINGLI_READING_VERSION:
        _require(groups, ("quant", "source_review", "mechanism", "timing", "domain"), "v6")
    elif reading_version == LIFE_DOMAIN_MINGLI_READING_VERSION:
        _require(groups, ("quant", "mechanism", "timing", "domain"), "v5")
        _forbid(groups, ("source_review",), "v5")
    elif reading_version == TIMING_MINGLI_READING_VERSION:
        _require(groups, ("quant", "mechanism", "timing"), "v4")
        _forbid(groups, ("source_review", "domain"), "v4")
    elif reading_version == MECHANISM_MINGLI_READING_VERSION:
        _require(groups, ("quant", "mechanism"), "v3")
        _forbid(groups, ("source_review", "timing", "domain"), "v3")
    elif reading_version == QUANT_MINGLI_READING_VERSION:
        _require(groups, ("quant",), "v2")
        _forbid(
            groups,
            ("source_review", "mechanism", "timing", "domain"),
            "v2",
        )
    elif reading_version == LEGACY_MINGLI_READING_VERSION:
        _forbid(
            groups,
            ("source_review", "quant", "mechanism", "timing", "domain"),
            "v1",
        )
    else:
        raise ValueError("mingli_reading_version_not_supported")


def reading_hash_exclusions(reading_version: str) -> set[str]:
    excluded = {"reading_ref", "reading_hash"}
    if reading_version == LIFE_DOMAIN_MINGLI_READING_VERSION:
        excluded.update(SOURCE_REVIEW_FIELDS)
    elif reading_version == TIMING_MINGLI_READING_VERSION:
        excluded.update(SOURCE_REVIEW_FIELDS | DOMAIN_FIELDS)
    elif reading_version == MECHANISM_MINGLI_READING_VERSION:
        excluded.update(SOURCE_REVIEW_FIELDS | TIMING_FIELDS | DOMAIN_FIELDS)
    elif reading_version == QUANT_MINGLI_READING_VERSION:
        excluded.update(SOURCE_REVIEW_FIELDS | MECHANISM_FIELDS | TIMING_FIELDS | DOMAIN_FIELDS)
    elif reading_version == LEGACY_MINGLI_READING_VERSION:
        excluded.update(
            SOURCE_REVIEW_FIELDS | QUANT_FIELDS | MECHANISM_FIELDS | TIMING_FIELDS | DOMAIN_FIELDS
        )
    return excluded


def _require(
    groups: Mapping[str, tuple[Any, ...]],
    names: tuple[str, ...],
    version_label: str,
) -> None:
    for name in names:
        if any(value is None for value in groups[name]):
            raise ValueError(f"mingli_reading_{version_label}_requires_{name}_evidence")


def _forbid(
    groups: Mapping[str, tuple[Any, ...]],
    names: tuple[str, ...],
    version_label: str,
) -> None:
    for name in names:
        if any(value is not None for value in groups[name]):
            raise ValueError(f"mingli_reading_{version_label}_cannot_bind_{name}_evidence")
