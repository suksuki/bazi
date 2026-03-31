"""
全息知识库控制器 (HKB Controller)
MVC Controller Layer - 负责全息知识库加载与解析
"""

import json
from pathlib import Path
from typing import Dict, Any, List


class HolographicKnowledgeController:
    """全息知识库控制器"""

    def __init__(self) -> None:
        self.knowledge_dir = Path(__file__).parent.parent / "knowledge" / "holographic_pattern"

    def list_available_patterns(self) -> List[Dict[str, Any]]:
        if not self.knowledge_dir.exists():
            return []
        result = []
        for path in sorted(self.knowledge_dir.glob("*_kb.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                result.append({
                    "pattern_id": data.get("pattern_id"),
                    "display_name": data.get("meta", {}).get("display_name"),
                    "chinese_name": data.get("meta", {}).get("chinese_name"),
                    "category": data.get("meta", {}).get("category"),
                    "path": str(path)
                })
            except (json.JSONDecodeError, OSError):
                continue
        return result

    def load_knowledge(self, pattern_id: str) -> Dict[str, Any]:
        path = self.knowledge_dir / f"{pattern_id}_kb.json"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
