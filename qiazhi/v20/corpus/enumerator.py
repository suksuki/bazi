from __future__ import annotations

from v20.core.constants import BRANCHES, STEMS
from v20.corpus.canonical_case import CanonicalCase


def sample_corpus_cases(limit: int = 12) -> tuple[CanonicalCase, ...]:
    rows: list[CanonicalCase] = []
    for index, stem in enumerate(STEMS):
        if len(rows) >= limit:
            break
        branch = BRANCHES[index % len(BRANCHES)]
        rows.append(
            CanonicalCase(
                case_id=f"v20.corpus.sample.{index:03d}",
                pillar_displays=(f"{stem}{branch}", "戊辰", "甲午", "辛酉"),
            )
        )
    return tuple(rows)
