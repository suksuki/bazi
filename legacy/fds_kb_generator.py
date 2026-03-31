#!/usr/bin/env python3
"""
FDS 全息知识库 (HKB) 自动化生成器
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from json_logic import jsonLogic
except ImportError:
    jsonLogic = None


REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")
HKB_CONFIG_PATH = Path("./config/hkb/hkb_params.json")
KNOWLEDGE_DIR = Path("./knowledge/holographic_pattern")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_registry(pattern_id: str) -> Dict[str, Any]:
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    data = load_json(registry_path)
    if data.get("topic") != "holographic_pattern":
        raise ValueError("无效的registry topic，必须为 holographic_pattern")
    return data


def load_manifest(pattern_id: str) -> Optional[Dict[str, Any]]:
    candidates = [
        MANIFEST_DIR / f"manifest_{pattern_id}.json",
        MANIFEST_DIR / f"manifest_{pattern_id.replace('-', '')}.json",
        MANIFEST_DIR / f"{pattern_id}.json"
    ]
    for path in candidates:
        if path.exists():
            return load_json(path)
    return None


def extract_mean_vector(registry_data: Dict[str, Any]) -> List[float]:
    anchors = registry_data.get("data", {}).get("feature_anchors", {})
    manifold = anchors.get("standard_manifold", {})
    mean_vector = manifold.get("mean_vector")
    if not mean_vector:
        raise ValueError("registry缺少standard_manifold.mean_vector")
    return mean_vector


def extract_covariance_matrix(registry_data: Dict[str, Any]) -> Optional[List[List[float]]]:
    anchors = registry_data.get("data", {}).get("feature_anchors", {})
    manifold = anchors.get("standard_manifold", {})
    return manifold.get("covariance_matrix")


def extract_subpattern_centroids(registry_data: Dict[str, Any]) -> Dict[str, List[float]]:
    """
    从registry提取子格局质心向量
    
    优先从feature_anchors.subpattern_centroids读取（永久物理锚点）
    """
    data = registry_data.get("data", {})
    anchors = data.get("feature_anchors", {})
    
    # 优先从feature_anchors读取
    subpattern_data = anchors.get("subpattern_centroids", {})
    if subpattern_data:
        centroids = {}
        for sub_id, sub_data in subpattern_data.items():
            if isinstance(sub_data, dict):
                centroid = sub_data.get("centroid_vector")
            elif isinstance(sub_data, list):
                centroid = sub_data
            else:
                continue
            if centroid and len(centroid) == 5:
                centroids[sub_id] = centroid
        if centroids:
            return centroids
    
    # 降级：从旧字段读取
    centroids = data.get("subpattern_centroids") or data.get("sub_pattern_centroids")
    return centroids if isinstance(centroids, dict) else {}


def axis_scores(mean_vector: List[float], axes: List[str]) -> Dict[str, float]:
    if len(mean_vector) != len(axes):
        raise ValueError("mean_vector维度与轴数量不一致")
    return {axis: float(value) for axis, value in zip(axes, mean_vector)}


def get_dominant_axes(scores: Dict[str, float], count: int) -> List[Tuple[str, float]]:
    return sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:count]


def evaluate_conditions(
    centroid: Dict[str, float],
    conditions: List[Dict[str, Any]],
    thresholds: Dict[str, Any]
) -> bool:
    for condition in conditions:
        axis = condition.get("axis")
        operator = condition.get("operator")
        threshold_key = condition.get("threshold_key")
        if axis not in centroid or threshold_key not in thresholds:
            return False
        threshold = thresholds[threshold_key]
        value = centroid[axis]
        if operator == ">":
            if not value > threshold:
                return False
        elif operator == ">=":
            if not value >= threshold:
                return False
        elif operator == "<":
            if not value < threshold:
                return False
        elif operator == "<=":
            if not value <= threshold:
                return False
        else:
            raise ValueError(f"未知操作符: {operator}")
    return True


def build_knowledge_entries(
    subpattern_centroids: Dict[str, List[float]],
    axes: List[str],
    rules: List[Dict[str, Any]],
    thresholds: Dict[str, Any],
    messages: Dict[str, str],
    subpattern_templates: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    构建知识条目，支持基于模板的动态生成
    
    优先使用subpattern_templates生成详细描述，降级使用rules和messages
    """
    entries = []
    
    # 如果有子格局模板，使用模板生成
    if subpattern_templates:
        for sub_id, centroid_vec in subpattern_centroids.items():
            if len(centroid_vec) != len(axes):
                continue
            
            template = subpattern_templates.get(sub_id)
            if not template:
                continue
            
            centroid_map = axis_scores(centroid_vec, axes)
            name = template.get("name", sub_id)
            desc_template = template.get("description_template", "")
            axis_analysis = template.get("axis_analysis", {})
            
            # 生成描述
            description = desc_template.format(
                name=name,
                e=centroid_map.get("E", 0),
                o=centroid_map.get("O", 0),
                m=centroid_map.get("M", 0),
                s=centroid_map.get("S", 0),
                r=centroid_map.get("R", 0),
                energy_desc=_get_axis_description(centroid_map.get("E", 0), axis_analysis.get("E", {}), "E"),
                stress_desc=_get_axis_description(centroid_map.get("S", 0), axis_analysis.get("S", {}), "S"),
                material_desc=_get_axis_description(centroid_map.get("M", 0), axis_analysis.get("M", {}), "M"),
                order_desc=_get_axis_description(centroid_map.get("O", 0), axis_analysis.get("O", {}), "O"),
                relation_desc=_get_axis_description(centroid_map.get("R", 0), axis_analysis.get("R", {}), "R")
            )
            
            entries.append({
                "pattern_id": sub_id,
                "name": name,
                "description": description,
                "centroid_vector": centroid_vec,
                "axis_scores": centroid_map,
                "source": "subpattern_template"
            })
    
    # 降级：使用rules和messages（保持向后兼容）
    if not entries:
        for rule in rules:
            pattern_id = rule.get("pattern_id")
            if pattern_id not in subpattern_centroids:
                continue
            centroid_vec = subpattern_centroids[pattern_id]
            if len(centroid_vec) != len(axes):
                continue
            centroid_map = axis_scores(centroid_vec, axes)
            conditions = rule.get("conditions", [])
            if evaluate_conditions(centroid_map, conditions, thresholds):
                message_key = rule.get("message_key")
                message = messages.get(message_key)
                if message:
                    entries.append({
                        "pattern_id": pattern_id,
                        "message": message,
                        "evidence": centroid_map,
                        "rule_id": rule.get("id")
                    })
    
    return entries


def _get_axis_description(value: float, analysis: Dict[str, str], axis: str) -> str:
    """根据轴值获取描述"""
    if not analysis:
        return ""
    
    if value >= 2.5:
        return analysis.get("high", "")
    elif value >= 1.5:
        return analysis.get("medium", "")
    else:
        return analysis.get("low", "")


def build_risk_notes(
    calibration_metrics: Dict[str, Any],
    thresholds: Dict[str, Any],
    messages: Dict[str, str]
) -> List[str]:
    notes = []
    iou_value = calibration_metrics.get("iou")
    iou_threshold = thresholds.get("iou_low")
    if iou_value is not None and iou_threshold is not None:
        if iou_value < iou_threshold:
            msg = messages.get("iou_low")
            if msg:
                notes.append(msg)
    return notes


def select_system_message(
    calibration_metrics: Dict[str, Any],
    thresholds: Dict[str, Any],
    system_messages: Dict[str, str]
) -> str:
    iou_value = calibration_metrics.get("iou")
    iou_threshold = thresholds.get("iou_low")
    if iou_value is not None and iou_threshold is not None:
        if iou_value < iou_threshold:
            return system_messages.get("iou_low", system_messages.get("default", ""))
    return system_messages.get("default", "")


def build_weights_matrix(manifest: Dict[str, Any], tmm_override: Dict[str, Any] | None = None) -> Tuple[List[str], List[List[float]]]:
    mapping = tmm_override or manifest.get("tensor_mapping_matrix", {})
    ten_gods = mapping.get("ten_gods", [])
    weights = mapping.get("weights", {})
    matrix = []
    for god in ten_gods:
        matrix.append(weights.get(god, []))
    return ten_gods, matrix


def calculate_5d_tensor(case_ten_gods: Dict[str, Any], ten_gods: List[str], matrix: List[List[float]]) -> List[float]:
    vec = [0.0 for _ in ten_gods]
    for idx, god in enumerate(ten_gods):
        if god in case_ten_gods:
            vec[idx] = float(case_ten_gods[god])
    tensor = [0.0 for _ in range(len(matrix[0]))]
    for i in range(len(matrix[0])):
        tensor[i] = sum(matrix[j][i] * vec[j] for j in range(len(ten_gods)))
    return tensor


def compute_subpattern_centroids(
    manifest_data: Dict[str, Any],
    data_path: Path
) -> Dict[str, List[float]]:
    if jsonLogic is None:
        print("⚠️ 缺少 json-logic-quibble 依赖，跳过子格局质心计算")
        return {}

    sub_defs = manifest_data.get("sub_pattern_definitions", {})
    if not sub_defs:
        return {}

    tmm_override = None
    try:
        from core.tensor_mapping_loader import load_tensor_mapping_matrix
        tmm_override, _ = load_tensor_mapping_matrix(manifest_data)
    except Exception:
        pass
    ten_gods, matrix = build_weights_matrix(manifest_data, tmm_override=tmm_override)
    accumulators: Dict[str, List[List[float]]] = {key: [] for key in sub_defs.keys()}

    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            for sub_id, sub_def in sub_defs.items():
                logic = sub_def.get("logic")
                if not logic:
                    continue
                try:
                    if jsonLogic(logic, case):
                        tensor = calculate_5d_tensor(case.get("ten_gods", {}), ten_gods, matrix)
                        accumulators[sub_id].append(tensor)
                except Exception:
                    continue

    centroids: Dict[str, List[float]] = {}
    for sub_id, tensors in accumulators.items():
        if not tensors:
            continue
        dims = len(tensors[0])
        centroid = [0.0 for _ in range(dims)]
        for tensor in tensors:
            for idx, val in enumerate(tensor):
                centroid[idx] += val
        count = float(len(tensors))
        centroids[sub_id] = [value / count for value in centroid]
    return centroids


def generate_kb(
    pattern_id: str,
    output_path: Optional[Path] = None,
    data_path: Optional[Path] = None
) -> Path:
    hkb_config = load_json(HKB_CONFIG_PATH)
    hkb = hkb_config.get("hkb", {})

    registry_data = load_registry(pattern_id)
    manifest_data = load_manifest(pattern_id)

    axes = ["E", "O", "M", "S", "R"]
    mean_vector = extract_mean_vector(registry_data)
    covariance_matrix = extract_covariance_matrix(registry_data)
    subpattern_centroids = extract_subpattern_centroids(registry_data)
    if data_path and manifest_data:
        computed_centroids = compute_subpattern_centroids(manifest_data, data_path)
        if computed_centroids:
            subpattern_centroids = computed_centroids

    scores = axis_scores(mean_vector, axes)
    dominant_count = int(hkb.get("dominant_axes_count"))
    dominant = get_dominant_axes(scores, dominant_count)

    axis_semantics = hkb.get("axis_semantics", {})
    dominant_axes = [
        {
            "axis": axis,
            "score": score,
            "semantics": axis_semantics.get(axis, [])
        }
        for axis, score in dominant
    ]

    calibration_metrics = registry_data.get("data", {}).get("calibration_metrics", {})
    thresholds = hkb.get("thresholds", {})
    messages = hkb.get("messages", {})
    system_messages = hkb.get("system_messages", {})

    knowledge_entries = build_knowledge_entries(
        subpattern_centroids,
        axes,
        hkb.get("rules", []),
        thresholds,
        messages,
        hkb.get("subpattern_templates")
    )

    risk_notes = build_risk_notes(calibration_metrics, thresholds, messages)
    system_message = select_system_message(calibration_metrics, thresholds, system_messages)

    meta_info = registry_data.get("data", {}).get("meta_info", {})
    classical_desc = None
    if manifest_data:
        classical_desc = manifest_data.get("classical_logic_rules", {}).get("description")

    knowledge_payload = {
        "topic": "holographic_knowledge",
        "schema_version": hkb_config.get("schema_version"),
        "pattern_id": pattern_id,
        "meta": {
            "display_name": meta_info.get("display_name"),
            "chinese_name": meta_info.get("chinese_name"),
            "category": meta_info.get("category"),
            "source_ref": meta_info.get("source_ref")
        },
        "anchors": {
            "mean_vector": mean_vector,
            "covariance_matrix": covariance_matrix
        },
        "physical_summary": {
            "axis_scores": scores,
            "dominant_axes": dominant_axes
        },
        "classical_alignment": {
            "description": classical_desc,
            "base_abundance": registry_data.get("data", {}).get("population_stats", {}).get("base_abundance")
        },
        "singularity_risk": {
            "calibration_metrics": calibration_metrics,
            "risk_notes": risk_notes
        },
        "knowledge_entries": knowledge_entries,
        "system_message": system_message
    }

    output_path = output_path or (KNOWLEDGE_DIR / f"{pattern_id}_kb.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(knowledge_payload, f, indent=2, ensure_ascii=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="FDS HKB 自动化生成器")
    parser.add_argument("--target", required=True, help="格局ID（如 A-01）")
    parser.add_argument("--output", help="输出文件路径（可选）")
    parser.add_argument("--data", help="数据文件路径（用于计算子格局质心）")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    data_path = Path(args.data) if args.data else None
    result = generate_kb(args.target, output_path, data_path)
    print(f"✅ HKB已生成: {result}")


if __name__ == "__main__":
    main()
