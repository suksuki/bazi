from __future__ import annotations

from itertools import combinations

from v30.contracts import V30Model
from v30.core.constants import (
    BRANCH_BREAK,
    BRANCH_CLASH,
    BRANCH_HARM,
    BRANCH_HARMONY,
    BRANCH_PUNISHMENT,
    THREE_HARMONY,
    THREE_MEETING,
    pair_key,
)
from v30.core.pillars import Pillar


class RelationHit(V30Model):
    relation_type: str
    branches: tuple[str, ...]
    positions: tuple[str, ...]
    layer: str = "natal"
    element: str = ""


def branch_relation_hits(pillars: dict[str, Pillar], *, layer: str = "natal") -> tuple[RelationHit, ...]:
    rows: list[RelationHit] = []
    branch_positions = [(position, pillar.branch) for position, pillar in pillars.items() if pillar.branch]
    for (left_pos, left_branch), (right_pos, right_branch) in combinations(branch_positions, 2):
        key = pair_key(left_branch, right_branch)
        if key in BRANCH_CLASH:
            rows.append(_pair_hit("clash", left_branch, right_branch, left_pos, right_pos, layer))
        if key in BRANCH_HARMONY:
            rows.append(_pair_hit("harmony", left_branch, right_branch, left_pos, right_pos, layer))
        if key in BRANCH_HARM:
            rows.append(_pair_hit("harm", left_branch, right_branch, left_pos, right_pos, layer))
        if key in BRANCH_BREAK:
            rows.append(_pair_hit("break", left_branch, right_branch, left_pos, right_pos, layer))
        if key in BRANCH_PUNISHMENT:
            rows.append(_pair_hit("punishment", left_branch, right_branch, left_pos, right_pos, layer))

    branches = {branch for _pos, branch in branch_positions}
    positions_by_branch = {branch: pos for pos, branch in branch_positions}
    for element, members in THREE_HARMONY.items():
        if members <= branches:
            rows.append(
                RelationHit(
                    relation_type="three_harmony",
                    branches=tuple(sorted(members)),
                    positions=tuple(positions_by_branch[branch] for branch in sorted(members)),
                    layer=layer,
                    element=element,
                )
            )
    for element, members in THREE_MEETING.items():
        if members <= branches:
            rows.append(
                RelationHit(
                    relation_type="three_meeting",
                    branches=tuple(sorted(members)),
                    positions=tuple(positions_by_branch[branch] for branch in sorted(members)),
                    layer=layer,
                    element=element,
                )
            )
    return tuple(rows)


def _pair_hit(
    relation_type: str,
    left_branch: str,
    right_branch: str,
    left_pos: str,
    right_pos: str,
    layer: str,
) -> RelationHit:
    return RelationHit(
        relation_type=relation_type,
        branches=(left_branch, right_branch),
        positions=(left_pos, right_pos),
        layer=layer,
    )
