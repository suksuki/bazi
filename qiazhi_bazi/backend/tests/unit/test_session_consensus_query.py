"""SessionConsensus 查询：同一 decision_key 仅保留 id 最大的一条。"""
from __future__ import annotations

from app.db.models import SessionConsensus
from app.services.helpers.session_consensus_query import fetch_latest_session_consensus_rows


class _FakeExec:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, rows):
        # 与 DB order_by(id DESC) 一致：先遍历到的为最新 id
        self._rows = sorted(rows, key=lambda r: -(r.id or 0))

    def exec(self, _stmt):
        return _FakeExec(self._rows)


def test_latest_row_wins_per_decision_key():
    rows = [
        SessionConsensus(id=1, session_id=9, decision_key="CF_FLOATING_DECAY", confirmed_value=0.1, reasoning="old"),
        SessionConsensus(id=3, session_id=9, decision_key="CF_FLOATING_DECAY", confirmed_value=0.2, reasoning="new"),
        SessionConsensus(id=2, session_id=9, decision_key="OTHER", confirmed_value=1.0, reasoning="x"),
    ]
    out = fetch_latest_session_consensus_rows(_FakeSession(rows), 9)
    by_key = {x["decision_key"]: x["confirmed_value"] for x in out}
    assert by_key["CF_FLOATING_DECAY"] == 0.2
    assert by_key["OTHER"] == 1.0
    assert len(out) == 2
