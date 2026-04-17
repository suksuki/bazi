from __future__ import annotations

from typing import Iterable

_FORBIDDEN_TERMS = (
    "sys.core",
    "fact_id",
)


def semantic_purity_ok(text: str, extra_terms: Iterable[str] | None = None) -> bool:
    s = str(text or "").lower()
    terms = list(_FORBIDDEN_TERMS)
    if extra_terms:
        terms.extend([str(x).lower() for x in extra_terms if str(x).strip()])
    return not any(t in s for t in terms)

