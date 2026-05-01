from __future__ import annotations

from v20.features.boundaries import boundary_for
from v20.graph.arbitration import arbitrate_paths
from v20.graph.schema import ChartGraph, RulePath
from v20.graph.scoring import score_path


def select_rule_paths(graph: ChartGraph, *, limit: int = 8) -> tuple[RulePath, ...]:
    candidates = tuple(_default_candidates())
    scored = tuple(score_path(graph, row) for row in candidates)
    selected = tuple(row for row in scored if row.score >= 0.24)
    return arbitrate_paths(selected, limit=limit)


def _default_candidates() -> list[RulePath]:
    return [
        RulePath("rulepath.strength.capacity", "strength", "Day-master capacity evidence", 0.28, ("pillar",), boundary_for("strength")),
        RulePath("rulepath.ten_god.visible", "ten_god", "Visible ten-god metadata", 0.26, ("ten_god:正官", "ten_god:偏财", "ten_god:食神"), boundary_for("ten_god")),
        RulePath("rulepath.branch.relations", "branch", "Branch relation layer review", 0.22, ("relation:clash", "relation:harmony", "relation:three_harmony"), boundary_for("branch")),
        RulePath("rulepath.wealth.material", "wealth", "Wealth material structure", 0.24, ("ten_god:正财", "ten_god:偏财"), boundary_for("wealth")),
        RulePath("rulepath.pattern.index", "pattern", "Pattern review index", 0.18, ("vault",), boundary_for("pattern")),
    ]
