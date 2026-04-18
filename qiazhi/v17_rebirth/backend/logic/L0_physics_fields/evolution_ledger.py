"""
V17.32：演化账本 (Evolution Ledger)。

记录每一个十神从 L0 BASE 到 L1 VECTOR 再到 PLUGIN 各阶段的能量变迁。
每次变更（append_entry）写入一条 LedgerEntry，最终以 JSON-safe dict 输出。

使用方式：
    ledger = EvolutionLedger()
    ledger.append_entry("伤官", 50.2, "L0_BASE", "干支初始能级")
    ledger.append_entry("伤官", 70.45, "L1_VECTOR_GAIN", "丁巳近合能级共振")
    raw = ledger.to_dict()
    # → {"伤官": [{"step": "L0_BASE", "val": 50.2, ...}, ...]}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LedgerEntry:
    """一条演化记录。"""
    step: str           # 阶段标签（L0_BASE / L1_VECTOR_GAIN / PLUGIN_xxx 等）
    val: float          # 变更后的当前值
    delta: float        # 本次变更量（首条为 0.0）
    reason: str         # 变更原因
    source: str = ""
    highlight_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "step": self.step,
            "val": round(self.val, 2),
            "reason": self.reason,
        }
        if abs(self.delta) > 1e-6:
            d["delta"] = round(self.delta, 2)
        if self.source:
            d["source"] = self.source
        if self.highlight_type:
            d["highlight_type"] = self.highlight_type
        return d


class EvolutionLedger:
    """
    十神演化账本。

    线程安全级别：单 session 内同步调用，不做跨线程锁。
    """

    def __init__(self) -> None:
        self._entries: Dict[str, List[LedgerEntry]] = {}

    def append_entry(
        self,
        ten_god_name: str,
        new_val: float,
        step: str,
        reason: str,
        *,
        source: str = "",
        highlight_type: str = "",
    ) -> None:
        """追加记录，每个十神上限为 8 条。"""
        name = str(ten_god_name or "").strip()
        if not name:
            return
        entries = self._entries.setdefault(name, [])
        prev_val = entries[-1].val if entries else 0.0
        delta = new_val - prev_val
        
        entries.append(LedgerEntry(
            step=str(step or "UNKNOWN"),
            val=float(new_val),
            delta=float(delta),
            reason=str(reason or ""),
            source=str(source or ("SRC_FLOW" if str(step or "") == "L1.5_FLOW_SETTLEMENT" else "")).strip(),
            highlight_type=str(highlight_type or ("cyan" if str(step or "") == "L1.5_FLOW_SETTLEMENT" else "")).strip(),
        ))
        
        # 审计：超过 8 条时，保留首条（初始能级）并丢弃中间过时的记录
        if len(entries) > 8:
            # 保留 [0] 和最新的 7 条
            self._entries[name] = [entries[0]] + entries[-7:]

    def bulk_snapshot(
        self,
        scores: Dict[str, float],
        step: str,
        reason: str,
    ) -> None:
        """
        对所有十神的当前值做一次批量快照。
        常用于 L0 BASE 阶段一次性初始化。
        """
        for god_name, val in scores.items():
            self.append_entry(god_name, float(val), step, reason)

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """输出 JSON-safe 的演化账本。"""
        return {
            name: [e.to_dict() for e in entries]
            for name, entries in self._entries.items()
            if entries
        }

    def names(self) -> List[str]:
        """返回已记录的所有十神名称。"""
        return list(self._entries.keys())

    def latest_val(self, ten_god_name: str) -> float:
        """返回某十神的最新值。"""
        entries = self._entries.get(str(ten_god_name or "").strip(), [])
        return entries[-1].val if entries else 0.0

    def total_delta(self, ten_god_name: str) -> float:
        """返回某十神从 L0 BASE 到当前的总变化量。"""
        entries = self._entries.get(str(ten_god_name or "").strip(), [])
        if len(entries) < 2:
            return 0.0
        return entries[-1].val - entries[0].val

    def __bool__(self) -> bool:
        return bool(self._entries)
