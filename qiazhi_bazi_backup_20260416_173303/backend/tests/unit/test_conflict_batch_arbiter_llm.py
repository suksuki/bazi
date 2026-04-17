from __future__ import annotations

import json

import pytest

from app.logic.brain.conflict_arbiter_llm import invoke_batch_conflict_arbiter_llm


class _FakeClient:
    def __init__(self, raw: str) -> None:
        self._raw = raw

    async def chat_with_telemetry(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        return self._raw, {}


@pytest.mark.asyncio
async def test_invoke_batch_conflict_arbiter_llm_success() -> None:
    raw = json.dumps(
        [
            {"index": 0, "decision": "p.a", "reason": "r0"},
            {"index": 1, "decision": "p.b", "reason": "r1"},
        ],
        ensure_ascii=False,
    )
    out = await invoke_batch_conflict_arbiter_llm(
        client=_FakeClient(raw),
        items=[
            {
                "conflict_summary": "c0",
                "candidate_plugins": ["p.a", "p.b"],
                "conflict_context": {"protocol": "arbitration_conflict_context.v1"},
            },
            {
                "conflict_summary": "c1",
                "candidate_plugins": ["p.a", "p.b"],
                "conflict_context": {"protocol": "arbitration_conflict_context.v1"},
            },
        ],
        lang="zh",
    )
    assert len(out.get("results") or []) == 2
    assert out["results"][0]["decision"] == "p.a"
    assert out["results"][1]["decision"] == "p.b"
    assert out["results"][0].get("certainty") == "CONFIDENT"
    assert out["results"][1].get("certainty") == "CONFIDENT"


@pytest.mark.asyncio
async def test_invoke_batch_conflict_arbiter_llm_truncates_huge_prompt() -> None:
    """V13.02：多冲突 + 超长 conflict_context 时 user 提示须落在软预算内，避免撑爆上下文窗口。"""
    rows = []
    for i in range(16):
        rows.append(
            {
                "conflict_summary": "摘要" * 120 + str(i),
                "candidate_plugins": ["p.a", "p.b"],
                "conflict_context": {"blob": "█" * 3500, "i": i},
            }
        )
    raw = json.dumps(
        [{"index": j, "decision": "p.a", "reason": "r", "certainty": "CONFIDENT"} for j in range(16)],
        ensure_ascii=False,
    )

    captured: dict = {}

    class _CapClient:
        async def chat_with_telemetry(self, messages, **kwargs):  # type: ignore[no-untyped-def]
            u = messages[1]["content"] if isinstance(messages[1], dict) else ""
            captured["user_len"] = len(str(u))
            return raw, {}

    out = await invoke_batch_conflict_arbiter_llm(client=_CapClient(), items=rows, lang="zh")
    assert len(out.get("results") or []) == 16
    assert int(captured.get("user_len") or 0) > 0
    assert int(captured.get("user_len") or 0) <= 32_000


@pytest.mark.asyncio
async def test_invoke_batch_conflict_arbiter_llm_parses_certainty() -> None:
    raw = json.dumps(
        [
            {"index": 0, "decision": "p.a", "reason": "r0", "certainty": "UNCERTAIN"},
            {"index": 1, "decision": "p.b", "reason": "r1", "certainty": "CONFIDENT"},
        ],
        ensure_ascii=False,
    )
    out = await invoke_batch_conflict_arbiter_llm(
        client=_FakeClient(raw),
        items=[
            {"conflict_summary": "c0", "candidate_plugins": ["p.a", "p.b"], "conflict_context": {}},
            {"conflict_summary": "c1", "candidate_plugins": ["p.a", "p.b"], "conflict_context": {}},
        ],
        lang="zh",
    )
    assert out["results"][0]["certainty"] == "UNCERTAIN"
    assert out["results"][1]["certainty"] == "CONFIDENT"


@pytest.mark.asyncio
async def test_invoke_batch_conflict_arbiter_llm_length_mismatch_returns_empty() -> None:
    raw = json.dumps([{"index": 0, "decision": "p.a", "reason": "only"}], ensure_ascii=False)
    out = await invoke_batch_conflict_arbiter_llm(
        client=_FakeClient(raw),
        items=[
            {"conflict_summary": "a", "candidate_plugins": ["p.a", "p.b"], "conflict_context": {}},
            {"conflict_summary": "b", "candidate_plugins": ["p.a", "p.b"], "conflict_context": {}},
        ],
        lang="zh",
    )
    assert out.get("results") == []
