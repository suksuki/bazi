from __future__ import annotations

from v30.core.constants import ELEMENTS, element_of_stem
from v30.core.pillars import Pillar
from v30.core.ten_gods import TenGodPosition


def element_distribution(
    pillars: dict[str, Pillar],
    hidden_ten_gods: tuple[TenGodPosition, ...],
) -> dict[str, float]:
    totals = {element: 0.0 for element in ELEMENTS}
    for pillar in pillars.values():
        element = element_of_stem(pillar.stem)
        if element in totals:
            totals[element] += 1.0
    for row in hidden_ten_gods:
        if row.element in totals:
            totals[row.element] += row.weight
    return {key: round(value, 3) for key, value in totals.items()}


def strongest_elements(distribution: dict[str, float]) -> tuple[str, ...]:
    if not distribution:
        return ()
    peak = max(distribution.values())
    return tuple(element for element, value in distribution.items() if value == peak)


def weakest_elements(distribution: dict[str, float]) -> tuple[str, ...]:
    if not distribution:
        return ()
    floor = min(distribution.values())
    return tuple(element for element, value in distribution.items() if value == floor)
