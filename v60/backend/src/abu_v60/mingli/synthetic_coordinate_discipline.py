from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import MingliAgentCasePacket

_CLAUSE_BREAK = re.compile(r"[，,。！？；;\n]")
_ASSIGNMENT = r"(?:为|是|乃|即|作|取|属|呈|：|:|=)?"


def month_command_coordinate_violations(
    value: Any,
    *,
    packet: MingliAgentCasePacket,
) -> tuple[dict[str, str], ...]:
    """Find explicit month-stem-as-month-command claims in synthetic prose.

    The checker is deliberately narrow: it rejects direct identity/assignment
    wording, while leaving relationship wording such as ``月令被己土所克`` or
    explicit negation to professional review.
    """

    month = next((item for item in packet.pillars if item.slot == "month"), None)
    if month is None:
        return ()
    stem = re.escape(month.stem)
    visible_ten_god = re.escape(month.visible_ten_god)
    prefix = rf"月令(?:本气|藏干|十神)?{_ASSIGNMENT}"
    stem_pattern = re.compile(rf"{prefix}(?:{visible_ten_god})?{stem}(?:金|木|水|火|土)?")
    label_pattern = re.compile(rf"{prefix}(?:{stem}(?:金|木|水|火|土)?)?{visible_ten_god}")
    findings: set[tuple[str, str]] = set()
    for text in _iter_text(value):
        for clause in _CLAUSE_BREAK.split(text):
            compact = re.sub(r"\s+", "", clause)
            if not compact or "月令" not in compact:
                continue
            for code, pattern in (
                ("MONTH_STEM_AS_MONTH_COMMAND", stem_pattern),
                ("MONTH_VISIBLE_TEN_GOD_AS_MONTH_COMMAND", label_pattern),
            ):
                match = pattern.search(compact)
                if match is None:
                    continue
                matched = match.group(0)
                if any(marker in matched for marker in ("不", "非", "勿", "莫")):
                    continue
                if compact[match.end() :].startswith("所"):
                    continue
                findings.add((code, compact[:96]))
    return tuple({"code": code, "excerpt": excerpt} for code, excerpt in sorted(findings))


def _iter_text(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_text(item)
    elif hasattr(value, "model_dump"):
        yield from _iter_text(value.model_dump(mode="json"))
    elif hasattr(value, "__dict__"):
        yield from _iter_text(vars(value))
