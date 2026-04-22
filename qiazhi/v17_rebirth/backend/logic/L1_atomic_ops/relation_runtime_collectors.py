"""Compatibility facade for L1 relation runtime collectors.

Phase 3 keeps this thin export layer so current callers can migrate without
re-introducing a second implementation stack.
"""

from __future__ import annotations

from v17_rebirth.backend.logic.L1_atomic_ops.relation_penalty_families import (
    collect_penalty_relation_deltas,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_special_families import (
    collect_control_relation_deltas,
    collect_stem_fusion_relation_deltas,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_structured_families import (
    collect_structured_relation_family_deltas,
)

__all__ = [
    "collect_structured_relation_family_deltas",
    "collect_penalty_relation_deltas",
    "collect_control_relation_deltas",
    "collect_stem_fusion_relation_deltas",
]
