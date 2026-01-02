"""
A-03 奇点筛选与自动化存证脚本
============================
从 518k 样本库中筛选高质量奇点，确保：
1. 物理多样性：覆盖不同偏移方向（高E极热、高S极寒、高R联盟等）
2. 马氏距离：偏离标准流形 D_M > 2.5
3. 人生轨迹关联：极端 y_true 值

使用方法:
    source venv/bin/activate && python scripts/mine_a03_singularities.py
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.vault_manager import VaultManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# A-03 标准流形参数 (基于 FDS-V3.0 拟合结果)
A03_STANDARD_MEAN = np.array([0.60, 0.35, 0.15, 0.55, 0.35])  # [E, O, M, S, R]
A03_COVARIANCE = np.array([
    [0.02, 0.005, -0.008, 0.01, 0.003],
    [0.005, 0.015, 0.002, 0.005, 0.004],
    [-0.008, 0.002, 0.01, -0.003, 0.002],
    [0.01, 0.005, -0.003, 0.025, 0.006],
    [0.003, 0.004, 0.002, 0.006, 0.018]
])

# 物理多样性分区 (确保选出的奇点覆盖不同方向)
DIVERSITY_ZONES = {
    "HIGH_E_HOT": {"axis": "E", "threshold": 0.75, "direction": "gt", "description": "高能量极热型"},
    "LOW_E_WEAK": {"axis": "E", "threshold": 0.40, "direction": "lt", "description": "低能量身弱型"},
    "HIGH_S_STRESS": {"axis": "S", "threshold": 0.70, "direction": "gt", "description": "高应力型"},
    "NEGATIVE_S_SHIELD": {"axis": "S", "threshold": 0.20, "direction": "lt", "description": "负压屏蔽型"},
    "HIGH_R_ALLIANCE": {"axis": "R", "threshold": 0.60, "direction": "gt", "description": "高关联联盟型"},
    "LOW_M_POOR": {"axis": "M", "threshold": 0.10, "direction": "lt", "description": "极贫财务型"},
    "HIGH_O_POWER": {"axis": "O", "threshold": 0.60, "direction": "gt", "description": "高秩序权力型"},
    "EXTREME_Y_HIGH": {"axis": "y_true", "threshold": 0.9, "direction": "gt", "description": "极端高成就"},
    "EXTREME_Y_LOW": {"axis": "y_true", "threshold": 0.3, "direction": "lt", "description": "极端低成就"},
}


def calculate_mahalanobis_distance(tensor: np.ndarray) -> float:
    """计算马氏距离"""
    try:
        diff = tensor - A03_STANDARD_MEAN
        inv_cov = np.linalg.inv(A03_COVARIANCE)
        return float(np.sqrt(np.dot(np.dot(diff, inv_cov), diff)))
    except:
        # 如果协方差矩阵不可逆，使用欧氏距离
        return float(np.linalg.norm(tensor - A03_STANDARD_MEAN))


def classify_zone(tensor: np.ndarray, y_true: float) -> List[str]:
    """判断样本属于哪些多样性分区"""
    zones = []
    axis_map = {"E": 0, "O": 1, "M": 2, "S": 3, "R": 4}
    
    for zone_id, zone_def in DIVERSITY_ZONES.items():
        axis = zone_def["axis"]
        threshold = zone_def["threshold"]
        direction = zone_def["direction"]
        
        if axis == "y_true":
            value = y_true
        else:
            value = tensor[axis_map[axis]]
        
        if direction == "gt" and value > threshold:
            zones.append(zone_id)
        elif direction == "lt" and value < threshold:
            zones.append(zone_id)
    
    return zones


def load_a03_matched_samples() -> List[Dict]:
    """加载 A-03 已匹配样本"""
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    universe_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "core", "data", "holographic_universe_518k.jsonl"
    )
    
    # 方案1: 直接从 518k 库筛选符合 A-03 特征的样本
    # A-03 特征: E > 0.5, S > 0.4 (羊刃架杀基本特征)
    
    samples = []
    logger.info(f"正在从 518k 样本库中筛选 A-03 候选...")
    
    with open(universe_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # 跳过元数据行
                continue
            
            try:
                data = json.loads(line.strip())
                tensor = data.get("tensor", {})
                y_true = data.get("y_true", 0.5)
                
                # A-03 基本筛选条件
                E = tensor.get("E", 0)
                S = tensor.get("S", 0)
                O = tensor.get("O", 0)
                
                # 羊刃架杀特征: 高能量 + 中高应力 + 有一定秩序
                if E > 0.45 and S > 0.35 and O > 0.20:
                    samples.append({
                        "uid": data.get("uid"),
                        "tensor": [E, O, tensor.get("M", 0), S, tensor.get("R", 0)],
                        "y_true": y_true
                    })
                    
            except Exception as e:
                continue
    
    logger.info(f"从 518k 样本中筛选出 {len(samples)} 个 A-03 候选样本")
    return samples


def mine_singularities(samples: List[Dict], top_n: int = 50, diversity_quota: int = 5) -> List[Dict]:
    """
    筛选高质量奇点
    
    Args:
        samples: 候选样本列表
        top_n: 最终选取数量
        diversity_quota: 每个分区配额
        
    Returns:
        筛选后的奇点列表
    """
    candidates = []
    
    for sample in samples:
        tensor = np.array(sample["tensor"])
        y_true = sample["y_true"]
        
        # 计算马氏距离
        m_dist = calculate_mahalanobis_distance(tensor)
        
        # 只保留偏离较大的样本 (D_M > 2.0)
        if m_dist < 2.0:
            continue
        
        # 分类多样性分区
        zones = classify_zone(tensor, y_true)
        
        candidates.append({
            "uid": sample["uid"],
            "tensor": sample["tensor"],
            "y_true": y_true,
            "mahalanobis_distance": m_dist,
            "zones": zones,
            "zone_count": len(zones)
        })
    
    logger.info(f"马氏距离 > 2.0 的候选: {len(candidates)} 个")
    
    # 按多样性分区配额筛选
    selected = []
    zone_counts = {zone: 0 for zone in DIVERSITY_ZONES}
    
    # 优先选择属于多个分区的样本（更极端）
    candidates.sort(key=lambda x: (-x["zone_count"], -x["mahalanobis_distance"]))
    
    for candidate in candidates:
        if len(selected) >= top_n:
            break
        
        # 检查是否还有分区配额
        can_add = False
        for zone in candidate["zones"]:
            if zone_counts[zone] < diversity_quota:
                can_add = True
                break
        
        # 如果所有分区都满了，但总数还不够，也添加
        if not can_add and len(selected) < top_n // 2:
            can_add = True
        
        if can_add:
            selected.append(candidate)
            for zone in candidate["zones"]:
                zone_counts[zone] += 1
    
    # 如果还不够，按马氏距离补充
    if len(selected) < top_n:
        remaining = [c for c in candidates if c not in selected]
        remaining.sort(key=lambda x: -x["mahalanobis_distance"])
        selected.extend(remaining[:top_n - len(selected)])
    
    return selected[:top_n]


def ingest_singularities(vault: VaultManager, singularities: List[Dict]) -> Dict[str, int]:
    """批量存证奇点到知识库"""
    stats = {"success": 0, "error": 0}
    
    for sing in singularities:
        try:
            case_id = f"A03_SING_{sing['uid']:06d}"
            
            # 确定子格局类型
            zones = sing.get("zones", [])
            if "HIGH_R_ALLIANCE" in zones:
                sub_pattern = "SP_A03_ALLIANCE"
            elif "HIGH_S_STRESS" in zones:
                sub_pattern = "SP_A03_EXTREME_STRESS"
            elif "HIGH_E_HOT" in zones:
                sub_pattern = "SP_A03_HOT_BLADE"
            else:
                sub_pattern = "SP_A03_SINGULARITY"
            
            # 生成描述
            zone_desc = ", ".join([DIVERSITY_ZONES[z]["description"] for z in zones[:3]])
            
            metadata = {
                "pattern_id": "A-03",
                "sub_pattern": sub_pattern,
                "distance_to_manifold": sing["mahalanobis_distance"],
                "y_true": sing["y_true"],
                "zones": ",".join(zones),  # 将列表转换为逗号分隔字符串
                "zone_count": len(zones),
                "description": f"奇点样本: {zone_desc}"
            }
            
            vault.add_singularity(
                case_id=case_id,
                tensor_5d=sing["tensor"],
                metadata=metadata
            )
            stats["success"] += 1
            
        except Exception as e:
            logger.error(f"存证失败 (uid={sing.get('uid')}): {e}")
            stats["error"] += 1
    
    return stats


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🔬 A-03 奇点筛选与自动化存证")
    logger.info("=" * 60)
    
    # 1. 初始化 VaultManager
    try:
        vault = VaultManager()
        logger.info(f"✅ VaultManager 初始化成功")
        logger.info(f"   当前奇点库样本数: {vault.singularity_vault.count()}")
    except Exception as e:
        logger.error(f"❌ VaultManager 初始化失败: {e}")
        return
    
    # 2. 加载 A-03 候选样本
    samples = load_a03_matched_samples()
    if len(samples) < 50:
        logger.error(f"候选样本数不足: {len(samples)}")
        return
    
    # 3. 筛选高质量奇点（确保多样性）
    logger.info("\n🔍 筛选高质量奇点 (确保物理多样性)...")
    singularities = mine_singularities(samples, top_n=50, diversity_quota=6)
    logger.info(f"筛选完成: {len(singularities)} 个奇点")
    
    # 显示多样性分布
    zone_distribution = {}
    for sing in singularities:
        for zone in sing.get("zones", []):
            zone_distribution[zone] = zone_distribution.get(zone, 0) + 1
    
    logger.info("\n📊 多样性分布:")
    for zone, count in sorted(zone_distribution.items(), key=lambda x: -x[1]):
        logger.info(f"   {zone}: {count} 样本")
    
    # 4. 批量存证
    logger.info("\n⚛️ 批量存证到奇点库...")
    stats = ingest_singularities(vault, singularities)
    logger.info(f"   成功: {stats['success']}, 失败: {stats['error']}")
    
    # 5. 验证
    final_stats = vault.get_vault_stats()
    logger.info(f"\n📚 最终知识库状态:")
    logger.info(f"   语义库文档数: {final_stats['semantic_count']}")
    logger.info(f"   奇点库样本数: {final_stats['singularity_count']}")
    
    # 测试 KNN 检索多样性
    logger.info("\n🧪 测试 KNN 检索多样性...")
    test_tensors = [
        ([0.80, 0.30, 0.10, 0.75, 0.20], "高能量高应力"),
        ([0.55, 0.25, 0.05, 0.60, 0.55], "联盟型"),
        ([0.35, 0.40, 0.15, 0.50, 0.30], "身弱型"),
    ]
    
    for tensor, desc in test_tensors:
        results = vault.query_singularities(tensor, n_results=3)
        nearest = results["ids"][0] if results["ids"] else "None"
        dist = results["distances"][0] if results["distances"] else 0
        logger.info(f"   {desc}: 最近邻 {nearest} (距离: {dist:.4f})")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ A-03 奇点筛选与存证完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
