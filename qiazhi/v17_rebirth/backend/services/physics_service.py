"""
V17.23-Red：PhysicsService — 会话张量注册表。

V17.23 变更：存储层从进程内 dict 迁移到 StateBackend（内存/Redis 双实现）。
上层 API 完全兼容，调用方无感知切换。
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Dict

from v17_rebirth.backend.services.physics_canonical import V17PhysicsMetadata
from v17_rebirth.infrastructure.state_backend import get_state_backend


class DataSovereigntyError(RuntimeError):
    """元数据主权失败：六柱不完整、未稳定或非法越权；须切断 LLM 通道。"""


PhysicalVoidError = DataSovereigntyError  # 兼容 V17.19 文档/旧 import 名


class PhysicsService:
    """
    会话级物理张量注册表（单写多读）。

    V17.23：存储后端替换为 StateBackend，默认内存语义不变；
    配置 QIAZHI_REDIS_URL 后自动升级为 Redis Hash（带 TTL=3600s）。
    """

    _LOCAL_LOCK = threading.RLock()
    _LOCAL_PHYSICS: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _norm_sid(session_id: str) -> str:
        s = str(session_id or "").strip()
        return s if s else "default"

    @classmethod
    def prime_local_tensor(cls, session_id: str, physics: Dict[str, Any]) -> None:
        sid = cls._norm_sid(session_id)
        with cls._LOCAL_LOCK:
            cls._LOCAL_PHYSICS[sid] = dict(physics or {})

    @classmethod
    def get_local_metadata(cls, session_id: str) -> Dict[str, Any]:
        sid = cls._norm_sid(session_id)
        with cls._LOCAL_LOCK:
            return dict(cls._LOCAL_PHYSICS.get(sid) or {})

    # --- 同步便捷包装（维持对外 classmethod 接口）---

    @classmethod
    def bind_session_tensor(cls, session_id: str, physics: Dict[str, Any]) -> None:
        """在门控通过后绑定；覆盖同 session 的旧张量。"""
        sid = cls._norm_sid(session_id)
        backend = get_state_backend()
        cls.prime_local_tensor(sid, physics)

        async def _bind() -> None:
            ok = await backend.set_physics(sid, physics)
            if not ok:
                raise DataSovereigntyError("physics_bind_unconfirmed")

        # 在同步上下文调用 — 若当前有事件循环则 schedule；否则 create loop（测试场景）
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_bind())
            else:
                loop.run_until_complete(_bind())
        except RuntimeError:
            # 无事件循环（纯同步测试）—— 使用新 loop
            asyncio.run(_bind())

    @classmethod
    async def abind_session_tensor(cls, session_id: str, physics: Dict[str, Any]) -> None:
        """异步版本绑定（stream_v17 主流程使用此版本，避免 ensure_future 时序问题）。"""
        sid = cls._norm_sid(session_id)
        cls.prime_local_tensor(sid, physics)
        ok = await get_state_backend().set_physics(sid, physics)
        if not ok:
            raise DataSovereigntyError("physics_bind_unconfirmed")

    @classmethod
    def release_session(cls, session_id: str) -> None:
        sid = cls._norm_sid(session_id)
        with cls._LOCAL_LOCK:
            cls._LOCAL_PHYSICS.pop(sid, None)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(get_state_backend().delete_physics(sid))
            else:
                loop.run_until_complete(get_state_backend().delete_physics(sid))
        except RuntimeError:
            asyncio.run(get_state_backend().delete_physics(sid))

    @classmethod
    async def arelease_session(cls, session_id: str) -> None:
        """异步释放（SSE 断流时使用）。"""
        with cls._LOCAL_LOCK:
            cls._LOCAL_PHYSICS.pop(cls._norm_sid(session_id), None)
        await get_state_backend().delete_physics(cls._norm_sid(session_id))

    @classmethod
    def get_metadata(cls, session_id: str) -> Dict[str, Any]:
        """
        圣殿宪法：Model 缓存只读出口（浅拷贝）。
        禁止用 Request Body 替代此结果。

        注意：同步接口。Redis 后端通过 asyncio.run 获取（适合非流协程场景）。
        流协程中请使用 aget_metadata()。
        """
        sid = cls._norm_sid(session_id)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在 async 上下文调用 — 此路径不应出现；提醒使用 aget_metadata
                import warnings
                warnings.warn(
                    "PhysicsService.get_metadata() called from running event loop. "
                    "Use 'await PhysicsService.aget_metadata()' instead.",
                    stacklevel=2,
                )
                # 暂时用内存快照兜底（RedisBackend 无法同步读）
                from v17_rebirth.infrastructure.state_backend import _BACKEND, MemoryStateBackend
                if isinstance(_BACKEND, MemoryStateBackend):
                    with _BACKEND._lock:  # noqa: SLF001
                        return dict(_BACKEND._physics.get(sid) or {})
                return cls.get_local_metadata(sid)
            out = loop.run_until_complete(get_state_backend().get_physics(sid))
            return out if out else cls.get_local_metadata(sid)
        except RuntimeError:
            out = asyncio.run(get_state_backend().get_physics(sid))
            return out if out else cls.get_local_metadata(sid)

    @classmethod
    async def aget_metadata(cls, session_id: str) -> Dict[str, Any]:
        """纯 async 版本（流协程主路径）。"""
        sid = cls._norm_sid(session_id)
        out = await get_state_backend().get_physics(sid)
        return out if out else cls.get_local_metadata(sid)

    @classmethod
    async def ensure_stability(
        cls,
        session_id: str,
        *,
        wait_sec: float = 3.0,
        poll_sec: float = 0.05,
        local_physics: Dict[str, Any] | None = None,
    ) -> None:
        """
        首帧 SNAPSHOT 前阻塞对齐 SSOT 元数据。

        V17.24 双重检查：
          1. 首先检查 v17_physics_stable 标记位（强路径）
          2. 若超时但四柱已存在，判定为「逻辑降级成功」而非 DataSovereigntyError
             （避免 hydration 线程轻微延迟导致误报物理因果缺失）
        禁止在元数据未稳时向下游发物理 SNAPSHOT / 开 LLM。
        """
        sid = cls._norm_sid(session_id)
        if isinstance(local_physics, dict) and local_physics:
            cls.prime_local_tensor(sid, local_physics)
        deadline = time.monotonic() + max(0.5, float(wait_sec))
        poll = max(0.02, min(0.5, float(poll_sec)))
        while time.monotonic() < deadline:
            md = await get_state_backend().get_physics(sid)
            gate = V17PhysicsMetadata(md if isinstance(md, dict) else {})
            if await gate.is_stable():
                return
            await asyncio.sleep(poll)
        # 超时后双重检查：若四柱完整，降级放行（勿误报物理因果缺失）
        from v17_rebirth.backend.services.physics_canonical import six_pillars_tensor_complete
        md_final = await get_state_backend().get_physics(sid)
        keys_found = list(md_final.keys())
        if six_pillars_tensor_complete(md_final):
            logging.getLogger(__name__).warning(
                "[V17-Physics] Session %s: v17_physics_stable=False but four_pillars complete — "
                "treating as degraded-stable. Keys in tensor: %s",
                sid, keys_found,
            )
            return
        local_final = local_physics if isinstance(local_physics, dict) and local_physics else cls.get_local_metadata(sid)
        if six_pillars_tensor_complete(local_final):
            logging.getLogger(__name__).warning(
                "[V17-Physics] Session %s: backend timed out, but local tensor is complete — "
                "forcing causal pass-through. Backend keys=%s local keys=%s",
                sid, keys_found, list((local_final or {}).keys()),
            )
            return
        logging.getLogger(__name__).error(
            "[V17-Physics] Session %s: ensure_stability FAILED. "
            "Tensor keys in backend: %s",
            sid, keys_found,
        )
        raise DataSovereigntyError("physics_metadata_unstable")

    @classmethod
    def get_current_pillars(cls, session_id: str) -> Dict[str, Any]:
        """自 get_metadata 派生的柱位视图：四柱 + 大运 + 流年 + flow_year。"""
        pt = cls.get_metadata(session_id)
        fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
        return {
            "four_pillars": dict(fp),
            "luck_pillar": pt.get("luck_pillar"),
            "flow_pillar": pt.get("flow_pillar"),
            "flow_year": pt.get("flow_year"),
        }

    @classmethod
    async def aget_current_pillars(cls, session_id: str) -> Dict[str, Any]:
        pt = await cls.aget_metadata(session_id)
        fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
        return {
            "four_pillars": dict(fp),
            "luck_pillar": pt.get("luck_pillar"),
            "flow_pillar": pt.get("flow_pillar"),
            "flow_year": pt.get("flow_year"),
        }

    @classmethod
    async def get_physics_keys(cls, session_id: str) -> list:
        """调试接口：返回已存储的张量顶层 key 列表（确认 Redis 写入是否成功）。"""
        return await get_state_backend().get_physics_keys(cls._norm_sid(session_id))
