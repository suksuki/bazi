from __future__ import annotations

from v20.graph.schema import RulePath


def arbitrate_paths(paths: tuple[RulePath, ...], *, limit: int = 8) -> tuple[RulePath, ...]:
    ordered = sorted(paths, key=lambda row: (row.score, row.domain, row.path_id), reverse=True)
    return tuple(ordered[:limit])
