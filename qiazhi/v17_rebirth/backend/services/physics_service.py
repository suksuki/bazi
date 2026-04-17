"""
V17.20：元数据主权在 Model 层 —— 会话级 physics_tensor 注册表。
LLM 组装须通过 PhysicsService.get_metadata(session_id) / get_current_pillars(session_id) 读取 Model 缓存，不从 HTTP Body 解析物理元数据。
V17.21：ensure_stability —— 首帧 SNAPSHOT 前阻塞对齐 SSOT 元数据。
"""
from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Dict

from v17_rebirth.backend.services.physics_canonical import V17PhysicsMetadata


class DataSovereigntyError(RuntimeError):
    """元数据主权失败：六柱不完整、未稳定或非法越权；须切断 LLM 通道。"""


PhysicalVoidError = DataSovereigntyError  # 兼容 V17.19 文档/旧 import 名


_lock = threading.RLock()
_SESSION_PHYSICS: Dict[str, Dict[str, Any]] = {}


class PhysicsService:
    """进程内会话张量注册（单写多读）；与 NDJSON session_id 对齐。"""

    @staticmethod
    def _norm_sid(session_id: str) -> str:
        s = str(session_id or "").strip()
        return s if s else "default"

    @classmethod
    def bind_session_tensor(cls, session_id: str, physics: Dict[str, Any]) -> None:
        """在门控通过后绑定；覆盖同 session 的旧张量。"""
        sid = cls._norm_sid(session_id)
        with _lock:
            _SESSION_PHYSICS[sid] = physics

    @classmethod
    def release_session(cls, session_id: str) -> None:
        sid = cls._norm_sid(session_id)
        with _lock:
            _SESSION_PHYSICS.pop(sid, None)

    @classmethod
    def get_metadata(cls, session_id: str) -> Dict[str, Any]:
        """圣殿宪法：Model 缓存只读出口（浅拷贝）。禁止用 Request Body 替代此结果。"""
        sid = cls._norm_sid(session_id)
        with _lock:
            return dict(_SESSION_PHYSICS.get(sid) or {})

    @classmethod
    async def ensure_stability(cls, session_id: str, *, wait_sec: float = 3.0, poll_sec: float = 0.05) -> None:
        """
        先注水、再发帧：轮询 SSOT 张量直至 V17PhysicsMetadata 稳定，或超时抛出 DataSovereigntyError。
        禁止在元数据未稳时向下游发物理 SNAPSHOT / 开 LLM。
        """
        sid = cls._norm_sid(session_id)
        deadline = time.monotonic() + max(0.5, float(wait_sec))
        poll = max(0.02, min(0.5, float(poll_sec)))
        while time.monotonic() < deadline:
            md = cls.get_metadata(sid)
            gate = V17PhysicsMetadata(md if isinstance(md, dict) else {})
            if await gate.is_stable():
                return
            await asyncio.sleep(poll)
        raise DataSovereigntyError("physics_metadata_unstable")

    @classmethod
    def get_current_pillars(cls, session_id: str) -> Dict[str, Any]:
        """
        自 get_metadata 派生的柱位视图：四柱 + 大运 + 流年 + flow_year。
        """
        pt = cls.get_metadata(session_id)
        fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
        return {
            "four_pillars": dict(fp),
            "luck_pillar": pt.get("luck_pillar"),
            "flow_pillar": pt.get("flow_pillar"),
            "flow_year": pt.get("flow_year"),
        }
