# FDS 基础设施 2.0 — 双核（RAG + SQL）结构化数仓
# 第 045 号指令：元数据层 SQLite + 特征计算层 DuckDB

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_DB = ROOT / "core" / "database" / "fds_registry.db"
PHYSICS_DB = ROOT / "core" / "database" / "fds_physics.duckdb"

__all__ = [
    "REGISTRY_DB",
    "PHYSICS_DB",
    "get_registry",
    "get_physics",
]


def get_registry():
    """获取 SQLite 元数据层连接（懒加载）。"""
    from core.database.fds_registry import FDSRegistry
    return FDSRegistry(REGISTRY_DB)


def get_physics():
    """获取 DuckDB 特征计算层连接（懒加载）。"""
    from core.database.fds_physics import FDSPhysics
    return FDSPhysics(PHYSICS_DB)
