"""语义标签工厂：将 Abs / η / gamma 等标量折叠为 [Verified Facts] 可用的离散标签（阈值走 physics_settings）。"""
from __future__ import annotations

from app.semantic_translator.labels import attach_semantic_labels_to_physics_meta, build_semantic_label_bundle
from app.semantic_translator.verdict_skeleton import build_verdict_skeleton

__all__ = [
    "attach_semantic_labels_to_physics_meta",
    "build_semantic_label_bundle",
    "build_verdict_skeleton",
]
