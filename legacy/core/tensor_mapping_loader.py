"""
FDS 张量映射矩阵加载器 (Tensor Mapping Matrix Loader)
======================================================
全局优先策略：优先使用 V4.0-BETA 真理校准矩阵，不存在时回退到 manifest/registry。

供 fds_inference_engine、fds_kb_generator 等统一使用。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_V4_PATH = _PROJECT_ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
_V5_PATH = _PROJECT_ROOT / "config" / "physics" / "tensor_mapping_matrix_V5.0_ALPHA.json"


def load_tensor_mapping_matrix(
    manifest: Dict[str, Any],
    registry: Dict[str, Any] | None = None,
    v4_path: Path | None = None,
    preferred_version: str | None = None,
) -> Tuple[Dict[str, Any], str]:
    """
    加载 TMM：可按 preferred_version 优先 V5.0-ALPHA 或 V4.0-BETA，否则 manifest，再否则 registry.data。

    preferred_version: "5.0-ALPHA" 时优先加载 V5 文件；None 或 "4.0-BETA" 时优先 V4。

    Returns:
        (tmm_dict, matrix_version)
    """
    paths_to_try: list[tuple[Path, str]] = []
    if preferred_version == "5.0-ALPHA" and _V5_PATH.exists():
        paths_to_try.append((_V5_PATH, "5.0-ALPHA"))
    paths_to_try.append((v4_path or _V4_PATH, "4.0-BETA"))
    for path, version in paths_to_try:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tmm = {
                "ten_gods": data.get("ten_gods", []),
                "dimensions": data.get("dimensions", ["E", "O", "M", "S", "R"]),
                "weights": data.get("weights", {}),
            }
            if tmm["weights"] and tmm["ten_gods"]:
                return tmm, data.get("version", version)
        except Exception:
            pass
    tmm = (
        (registry or {}).get("data", {}).get("tensor_mapping_matrix")
        or manifest.get("tensor_mapping_matrix")
    )
    if tmm:
        return tmm, "3.0"
    raise ValueError("tensor_mapping_matrix not found in V4 path, manifest or registry")


def get_matrix_version_used(
    manifest: Dict[str, Any],
    registry: Dict[str, Any] | None = None,
    v4_path: Path | None = None,
    preferred_version: str | None = None,
) -> str:
    """仅返回当前会使用的矩阵版本号，不加载完整 TMM。"""
    if preferred_version == "5.0-ALPHA" and _V5_PATH.exists():
        try:
            with open(_V5_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("weights") and d.get("ten_gods"):
                return d.get("version", "5.0-ALPHA")
        except Exception:
            pass
    path = v4_path or _V4_PATH
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("weights") and d.get("ten_gods"):
                return d.get("version", "4.0-BETA")
        except Exception:
            pass
    return "3.0"
