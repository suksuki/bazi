from __future__ import annotations

import hashlib


def anonymous_ref(value: object, prefix: str) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:c2a:{digest}"
