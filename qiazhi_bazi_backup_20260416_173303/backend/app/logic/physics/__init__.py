"""物理场域辅助逻辑（地支互动解析等），与 ``skills/physics_calculations`` 纯算术解耦。"""

from app.logic.physics.branch_interactions import build_branch_interactions

__all__ = ["build_branch_interactions"]
