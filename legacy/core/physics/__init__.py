# core/physics — FDS 物理层（动态时空位移、流形捕获）
# 第 049/050 号 · SOP V5.6：引透、地理阻尼λ、刑冲合化、格局对撞态、RAG 应灾参数。

from core.physics.dynamic_engine import (
    compute_dynamic_tensor,
    manifold_capture,
    collision_warning,
    load_config,
)

__all__ = [
    "compute_dynamic_tensor",
    "manifold_capture",
    "collision_warning",
    "load_config",
]
