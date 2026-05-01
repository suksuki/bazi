from __future__ import annotations


def bounded_confidence(*values: float, floor: float = 0.18, ceiling: float = 0.88) -> float:
    total = sum(max(0.0, value) for value in values)
    return round(max(floor, min(ceiling, total)), 3)
