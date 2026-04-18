"""
V17.99: 插件规范校验器 (Spec Validator)
基于 V17_SKILL_MANIFEST 协议，确保所有逻辑插件符合物理常数解耦与矢量结算契约。
"""
import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from v17_rebirth.paths import V17_REBIRTH_ROOT

LOGIC_ROOT = V17_REBIRTH_ROOT / "backend" / "logic"

class SpecValidator:
    @staticmethod
    def validate_plugin_file(file_path: Path) -> Dict[str, Any]:
        """扫描单个 Python 文件，提取并校验 V17 规范元数据。"""
        results = {
            "valid": False,
            "id": None,
            "manifest": {},
            "params": {},
            "errors": []
        }
        
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            # 1. 寻找 V17_SKILL_MANIFEST (通常是 dict 或 docstring)
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "V17_SKILL_MANIFEST":
                            try:
                                # 处理简单的 dict 定义
                                if isinstance(node.value, ast.Dict):
                                    results["manifest"] = ast.literal_eval(node.value)
                                    results["id"] = results["manifest"].get("id")
                            except Exception as e:
                                results["errors"].append(f"Manifest parse error: {e}")
                
                # 2. 寻找 DECLARED_PARAMS
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "DECLARED_PARAMS":
                            try:
                                if isinstance(node.value, ast.Dict):
                                    results["params"] = ast.literal_eval(node.value)
                            except Exception as e:
                                results["errors"].append(f"Params parse error: {e}")
            
            # 3. 校验契约接口 (是否有 execute_vector_physics 或 collect_v17_facts)
            has_contract = False
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name in ("execute_vector_physics", "collect_v17_facts"):
                            has_contract = True
                            break
            
            if not has_contract:
                # 兼容旧版写法：检查模块级函数或 Spec 类
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and node.name == "collect_v17_facts":
                        has_contract = True
            
            if results["manifest"] and has_contract:
                results["valid"] = True
            elif not results["manifest"]:
                results["errors"].append("Missing V17_SKILL_MANIFEST")
            
        except Exception as e:
            results["errors"].append(f"File parse failed: {e}")
            
        return results

    @classmethod
    def scan_all_plugins(cls) -> List[Dict[str, Any]]:
        """扫描全量逻辑目录。"""
        all_results = []
        for py_file in LOGIC_ROOT.rglob("*.py"):
            if py_file.name.startswith("_"): continue
            res = cls.validate_plugin_file(py_file)
            res["file_rel"] = str(py_file.relative_to(LOGIC_ROOT))
            all_results.append(res)
        return all_results

def get_skill_registry_path() -> Path:
    reg_dir = V17_REBIRTH_ROOT / "backend" / "logic" / "configs"
    reg_dir.mkdir(parents=True, exist_ok=True)
    return reg_dir / "v17_skill_registry.json"

def persist_skill_library():
    """将扫描结果持久化到技能库（替代 .db 以简化部署）。"""
    results = SpecValidator.scan_all_plugins()
    registry_path = get_skill_registry_path()
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results
