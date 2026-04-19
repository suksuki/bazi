import json
from pathlib import Path
from typing import Any, Dict
from v17_rebirth.paths import V17_REBIRTH_ROOT

_CACHE: Dict[str, Any] = {}

def get_v17_constants(flatten: bool = False) -> Dict[str, Any]:
    """获取 V17 宇宙常数总线。"""
    cfg_path = V17_REBIRTH_ROOT / "backend" / "logic" / "configs" / "v17_core_constants.json"
    try:
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f).get("constants", {})
                if not flatten:
                    return data
                
                # 扁平化处理便于快速查找
                flat = {}
                for k, v in data.items():
                    if isinstance(v, dict) and k != "INDUCTION_MAP":
                        flat.update(v)
                    else:
                        flat[k] = v
                return flat
    except Exception:
        pass
    return {}

def get_constant(key: str, fallback: float, plugin_id: str = None) -> float:
    """获取并净化数值常数。优先级：插件本地覆盖 > 全局常量。"""
    # 1. 检查插件本地覆盖
    if plugin_id:
        local_cfg = get_plugin_config(plugin_id)
        if key in local_cfg:
            try:
                return round(float(local_cfg[key]), 4)
            except (ValueError, TypeError):
                pass

    # 2. 从全局扁平化总线查找
    constants = get_v17_constants(flatten=True)
    val = constants.get(key)
    
    # 3. 处理嵌套映射 (如 INDUCTION_MAP 中的 QI_SHA)
    if val is None:
        ind_map = constants.get("INDUCTION_MAP", {})
        if isinstance(ind_map, dict):
            val = ind_map.get(key)

    if val is None:
        return fallback

    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return fallback

def get_plugin_config(plugin_id: str) -> Dict[str, Any]:
    """获取特定插件的局部裁量配置。"""
    cfg_path = V17_REBIRTH_ROOT / "backend" / "logic" / "configs" / f"{plugin_id}.json"
    try:
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def resolve_config_number(value: Any, fallback: float = 0.0) -> float:
    """解析插件配置中的数字或 ref(global.KEY) 形式。"""
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    text = str(value or "").strip()
    if text.startswith("ref(global.") and text.endswith(")"):
        key = text[len("ref(global."):-1].strip()
        return get_constant(key, fallback)
    try:
        return round(float(text), 4)
    except (TypeError, ValueError):
        return round(float(fallback), 4)
