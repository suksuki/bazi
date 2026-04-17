"""
V17.23-Red：StateBackend 协议层。

提供两种实现：
  - MemoryStateBackend  — 进程内（开发 / 测试 / 单 worker 生产）
  - RedisStateBackend   — Redis Standalone / Sentinel（多 worker 生产）

上层代码（stream_v17, physics_service）统一面向 StateBackend 接口，
不直接持有 asyncio.Queue 或 dict。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

_log = logging.getLogger(__name__)

# ─── 常量 ────────────────────────────────────────────────────────────────────

PHYSICS_TTL_SEC: int = 3600  # 会话张量 TTL（1小时）
ACTION_QUEUE_DEPTH: int = 20  # 最大 action 积压深度

# ─── Redis key 构造器 ─────────────────────────────────────────────────────────

def _physics_key(session_id: str) -> str:
    return f"V17:SESSION:{session_id}:PHYSICS"


def _action_channel(session_id: str) -> str:
    return f"V17:SESSION:{session_id}:ACTIONS"


# ─── 抽象接口 ─────────────────────────────────────────────────────────────────

class StateBackend(ABC):
    """V17 分布式状态后端协议。"""

    # --- Physics Tensor (Hash, TTL) ---

    @abstractmethod
    async def set_physics(self, session_id: str, tensor: Dict[str, Any]) -> bool:
        """写入物理张量（覆盖 + 刷新 TTL），返回写入确认。"""

    @abstractmethod
    async def get_physics(self, session_id: str) -> Dict[str, Any]:
        """读取物理张量快照（不存在则返回空 dict）。"""

    @abstractmethod
    async def delete_physics(self, session_id: str) -> None:
        """释放会话张量（SSE 断流后调用）。"""

    @abstractmethod
    async def get_physics_keys(self, session_id: str) -> List[str]:
        """返回张量顶层 key 列表（调试用：确认数据是否写入）。"""
        return []

    # --- Action Pub/Sub ---

    @abstractmethod
    async def publish_action(self, session_id: str, event: Dict[str, Any]) -> None:
        """向 session 频道发布 action 事件。"""

    @abstractmethod
    @asynccontextmanager
    async def subscribe_actions(self, session_id: str) -> AsyncIterator["asyncio.Queue[Dict[str, Any]]"]:
        """
        上下文管理器：订阅 session 频道，返回 asyncio.Queue。
        退出时自动取消订阅（无论 sse 正常结束还是异常断流）。
        """
        # 子类实现；此处仅用于类型标注
        yield asyncio.Queue()  # type: ignore[misc]

    # --- 健康检查 ---

    async def ping(self) -> bool:
        return True


# ─── 内存实现（开发 / 测试 / 单机兜底）────────────────────────────────────────

class MemoryStateBackend(StateBackend):
    """
    进程内实现，与旧 _SESSION_PHYSICS / _SESSION_QUEUES 语义完全等价。
    在 QIAZHI_REDIS_URL 未配置时自动启用。

    ⚠️  多 worker 进程下仍然隔离，仅用于单 worker 或开发模式。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._physics: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, asyncio.Queue[Dict[str, Any]]] = {}

    async def set_physics(self, session_id: str, tensor: Dict[str, Any]) -> bool:
        with self._lock:
            # 与 Redis 后端保持一致：做 JSON 往返清洗，消除 datetime 等非标准类型
            try:
                clean = json.loads(json.dumps(tensor, default=str))
            except (TypeError, ValueError) as exc:
                _log.error(
                    "[V17-State:Memory] Physics tensor serialization failed for session=%s: %s",
                    session_id, exc,
                )
                clean = {}
            self._physics[session_id] = clean
        return True

    async def get_physics(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._physics.get(session_id) or {})

    async def delete_physics(self, session_id: str) -> None:
        with self._lock:
            self._physics.pop(session_id, None)

    async def get_physics_keys(self, session_id: str) -> List[str]:
        with self._lock:
            return list((self._physics.get(session_id) or {}).keys())

    async def publish_action(self, session_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            q = self._queues.setdefault(session_id, asyncio.Queue())
        # 溢出保护
        if q.qsize() >= ACTION_QUEUE_DEPTH:
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
        await q.put(event)

    @asynccontextmanager
    async def subscribe_actions(self, session_id: str) -> AsyncIterator[asyncio.Queue[Dict[str, Any]]]:
        with self._lock:
            q = self._queues.setdefault(session_id, asyncio.Queue())
        try:
            yield q
        finally:
            # 内存模式：队列保留（SSE 重连后可继续消费）
            pass


# ─── Redis 实现 ───────────────────────────────────────────────────────────────

class RedisStateBackend(StateBackend):
    """
    基于 redis.asyncio（redis-py ≥ 4.2）的生产后端。

    Physics Tensor：存为 Redis String（JSON 序列化），TTL = PHYSICS_TTL_SEC。
    Action Pub/Sub：每 session 一个频道，SSE 协程作为订阅方。

    可无缝升级到 Redis Sentinel（修改连接 URL 即可），
    Cluster 模式需另行适配 Pub/Sub 槽位（未来扩展点）。
    """

    def __init__(self, redis_url: str) -> None:
        try:
            import redis.asyncio as aioredis  # redis-py >= 4.2
        except ImportError as e:
            raise RuntimeError(
                "RedisStateBackend requires 'redis[asyncio]'. "
                "Run: pip install 'redis[asyncio]>=4.6'"
            ) from e
        self._url = redis_url
        self._client: "aioredis.Redis" = aioredis.from_url(  # type: ignore[attr-defined]
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        _log.info("[V17-Redis] RedisStateBackend initialized: %s", redis_url.split("@")[-1])

    # --- Physics ---

    async def set_physics(self, session_id: str, tensor: Dict[str, Any]) -> bool:
        key = _physics_key(session_id)
        # V17.24：强化序列化器——先用 default=str 兜住所有非标准类（datetime/Decimal 等），
        # 再 json.loads 往返清洗，确保写入 Redis 的是纯 JSON 兼容 dict。
        try:
            clean = json.loads(json.dumps(tensor, default=str))
        except (TypeError, ValueError) as exc:
            # 记录具体失败字段，方便 causal trace 定位
            bad_keys = [
                k for k, v in (tensor or {}).items()
                if not self._is_json_safe(v)
            ]
            _log.error(
                "[V17-Redis] Physics tensor serialization FAILED for session=%s: %s. "
                "Problematic top-level keys: %s",
                session_id, exc, bad_keys,
            )
            # 降级：只保存可安全序列化的顶层字段
            clean = {}
            for k, v in (tensor or {}).items():
                try:
                    json.dumps(v, default=str)
                    clean[k] = json.loads(json.dumps(v, default=str))
                except Exception:  # noqa: BLE001
                    _log.warning("[V17-Redis] Dropping field '%s' from tensor for session=%s", k, session_id)
        stored = await self._client.set(key, json.dumps(clean, ensure_ascii=False), ex=PHYSICS_TTL_SEC)
        _log.debug(
            "[V17-Redis] set_physics session=%s keys=%s stored=%s",
            session_id, list(clean.keys()), bool(stored),
        )
        return bool(stored)

    @staticmethod
    def _is_json_safe(v: Any) -> bool:
        try:
            json.dumps(v)
            return True
        except (TypeError, ValueError):
            return False

    async def get_physics(self, session_id: str) -> Dict[str, Any]:
        key = _physics_key(session_id)
        raw = await self._client.get(key)
        if not raw:
            _log.debug("[V17-Redis] get_physics session=%s → MISS (key not found)", session_id)
            return {}
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            _log.error("[V17-Redis] get_physics session=%s → JSON decode error", session_id)
            return {}

    async def delete_physics(self, session_id: str) -> None:
        await self._client.delete(_physics_key(session_id))

    async def get_physics_keys(self, session_id: str) -> List[str]:
        """返回 Redis 中存储的张量顶层 key 列表（调试用）。"""
        data = await self.get_physics(session_id)
        return list(data.keys())

    # --- Pub/Sub ---

    async def publish_action(self, session_id: str, event: Dict[str, Any]) -> None:
        channel = _action_channel(session_id)
        await self._client.publish(channel, json.dumps(event, ensure_ascii=False))

    @asynccontextmanager
    async def subscribe_actions(self, session_id: str) -> AsyncIterator[asyncio.Queue[Dict[str, Any]]]:
        """
        订阅 Redis 频道，将消息中继到 asyncio.Queue 供 SSE 生成器消费。
        context 退出时取消订阅并停止中继 task。
        """
        import redis.asyncio as aioredis  # noqa: PLC0415

        channel = _action_channel(session_id)
        q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        # 使用独立连接做 Pub/Sub（redis-py 要求独立连接）
        pubsub_client: aioredis.Redis = aioredis.from_url(  # type: ignore[attr-defined]
            self._url,
            encoding="utf-8",
            decode_responses=True,
        )
        psub = pubsub_client.pubsub()
        await psub.subscribe(channel)

        async def _relay() -> None:
            try:
                async for msg in psub.listen():
                    if msg is None:
                        continue
                    if msg.get("type") != "message":
                        continue
                    raw = msg.get("data", "")
                    try:
                        event = json.loads(raw)
                        if not isinstance(event, dict):
                            continue
                        if q.qsize() >= ACTION_QUEUE_DEPTH:
                            try:
                                q.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                        await q.put(event)
                    except (json.JSONDecodeError, TypeError):
                        pass
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # noqa: BLE001
                _log.warning("[V17-Redis] Pub/Sub relay error: %s", exc)

        relay_task = asyncio.create_task(_relay(), name=f"v17_pubsub_{session_id}")
        try:
            yield q
        finally:
            relay_task.cancel()
            try:
                await relay_task
            except (asyncio.CancelledError, Exception):
                pass
            try:
                await psub.unsubscribe(channel)
                await psub.close()
                await pubsub_client.aclose()
            except Exception:  # noqa: BLE001
                pass

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:  # noqa: BLE001
            return False


# ─── 工厂函数（模块级单例）────────────────────────────────────────────────────

_BACKEND: Optional[StateBackend] = None
_BACKEND_LOCK = threading.Lock()


def get_state_backend() -> StateBackend:
    """
    返回进程级单例 StateBackend。

    路由策略：
      - QIAZHI_REDIS_URL 已配置 → RedisStateBackend
      - 否则                    → MemoryStateBackend（并打印警告）
    """
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND
    with _BACKEND_LOCK:
        if _BACKEND is not None:
            return _BACKEND
        redis_url = str(os.getenv("QIAZHI_REDIS_URL", "") or "").strip()
        if redis_url:
            try:
                _BACKEND = RedisStateBackend(redis_url)
                _log.info("[V17-State] Using RedisStateBackend")
            except Exception as exc:  # noqa: BLE001
                _log.error(
                    "[V17-State] RedisStateBackend init failed (%s), falling back to MemoryStateBackend", exc
                )
                _BACKEND = MemoryStateBackend()
        else:
            _log.warning(
                "[V17-State] QIAZHI_REDIS_URL not set — using MemoryStateBackend. "
                "Multi-worker Action signals WILL NOT cross process boundaries. "
                "Set QIAZHI_REDIS_URL=redis://127.0.0.1:6379/0 for production."
            )
            _BACKEND = MemoryStateBackend()
        return _BACKEND
