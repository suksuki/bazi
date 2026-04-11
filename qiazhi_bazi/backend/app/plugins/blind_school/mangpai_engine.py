"""盲派灵魂级算子聚合层：具体规则见 rules/ 微模块。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.plugins.blind_school.rules.rule_host_guest import compute_causal_dividend_index, host_guest_chip_logs
from app.plugins.blind_school.rules.rule_pierce import pierce_chip_logs_from_work_vectors, scan_six_harm_points
from app.plugins.blind_school.rules.rule_standard_overlap import standard_overlap_chip_logs
from app.plugins.blind_school.rules.rule_tomb import tomb_chip_logs

__all__ = ["scan_six_harm_points", "compute_causal_dividend_index", "merge_mangpai_chip_logs"]


def merge_mangpai_chip_logs(
    *,
    work_vectors: List[Dict[str, Any]],
    feature_flags: Dict[str, Any],
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
) -> List[str]:
    """聚合需写入前端的 chip 日志（前端再写入 result_logs）。"""
    logs: List[str] = []
    if feature_flags.get("enable_pierce_harm", True):
        logs.extend(pierce_chip_logs_from_work_vectors(work_vectors))
    if feature_flags.get("enable_tomb_vault", True):
        logs.extend(tomb_chip_logs(metadata))
    if feature_flags.get("enable_host_guest_bonus", True):
        logs.extend(host_guest_chip_logs(physics_tensor))
    if feature_flags.get("enable_standard_overlap", True):
        logs.extend(standard_overlap_chip_logs(physics_tensor=physics_tensor))
    return logs
