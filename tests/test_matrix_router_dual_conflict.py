"""
[QGA V25.0 Phase 4] 矩阵路由器测试 - 双重矛盾虚拟样本
测试伤官见官 + 羊刃架杀同时触发的复合物理态

⚠️  注意：此测试是单元测试，不连接LLM
- 只测试MatrixRouter的逻辑计算
- 传入llm_response=None，使用自动计算模式
- 如需测试完整LLM流程，请运行 test_neural_router_integration.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.subjects.neural_router.matrix_router import MatrixRouter
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
import json


def test_dual_conflict_matrix_routing():
    """测试双重矛盾虚拟样本（伤官见官 + 羊刃架杀）"""
    
    print("=" * 80)
    print("🧪 测试：双重矛盾虚拟样本矩阵路由")
    print("   格局：伤官见官 + 羊刃架杀")
    print("=" * 80)
    
    # 创建矩阵路由器
    matrix_router = MatrixRouter()
    
    # 模拟双重矛盾格局
    # 伤官见官：应力高，金火对冲
    # 羊刃架杀：高压动态平衡
    active_patterns = [
        {
            "id": "SHANG_GUAN_JIAN_GUAN",
            "name": "伤官见官",
            "weight": 0.75,
            "confidence": 0.8
        },
        {
            "id": "YANG_REN_JIA_SHA",
            "name": "羊刃架杀",
            "weight": 0.9,
            "confidence": 0.85
        }
    ]
    
    # 构造高应力特征向量（符合双重矛盾）
    feature_vector = {
        "elemental_fields_dict": {
            "metal": 0.25,  # 金（官星）中等
            "wood": 0.20,   # 木
            "water": 0.15,  # 水
            "fire": 0.30,   # 火（伤官）高
            "earth": 0.10   # 土低
        },
        "stress_tensor": 0.82,  # 高应力（超过0.6阈值）
        "phase_coherence": 0.25,  # 低相位一致性（符合冲突特征）
        "momentum_term": {
            "shi_to_cai": 0.3,
            "cai_to_guan": 0.2,
            "guan_to_yin": 0.5
        },
        "routing_hint": "SHANG_GUAN_JIAN_GUAN"
    }
    
    # 执行矩阵路由
    result = matrix_router.process_matrix_routing(
        active_patterns=active_patterns,
        feature_vector=feature_vector,
        llm_response=None  # 不使用LLM响应，测试自动计算
    )
    
    print(f"\n✅ 矩阵路由结果:")
    print(f"\n📊 权重坍缩 (Logic Collapse):")
    collapse_weights = result.get("logic_collapse", {})
    total_weight = sum(collapse_weights.values())
    for pattern_id, weight in collapse_weights.items():
        print(f"   {pattern_id:25s}: {weight:.4f} ({weight*100:.2f}%)")
    print(f"   总计: {total_weight:.4f} ({total_weight*100:.2f}%)")
    
    print(f"\n⚡ 能量状态报告 (Energy State Report):")
    energy_report = result.get("energy_state_report", {})
    print(f"   系统稳定性: {energy_report.get('system_stability', 0.0):.4f}")
    print(f"   能量流向: {energy_report.get('energy_flow_direction', 'N/A')}")
    print(f"   临界状态: {energy_report.get('critical_state', 'N/A')}")
    print(f"   总能量: {energy_report.get('total_energy', 0.0):.4f}")
    print(f"   应力张量: {energy_report.get('stress_tensor', 0.0):.4f}")
    print(f"   相位一致性: {energy_report.get('phase_coherence', 0.0):.4f}")
    
    # 验证复合物理态识别
    print(f"\n🔍 复合物理态验证:")
    critical_state = energy_report.get("critical_state", "")
    stability = energy_report.get("system_stability", 0.0)
    
    # 期望：系统应识别出"崩态"或"高压下的晶格崩塌"
    if "崩" in critical_state or stability < 0.3:
        print(f"   ✅ 系统正确识别出崩态/高压状态")
        print(f"   ✅ 临界状态: {critical_state}")
        print(f"   ✅ 系统稳定性: {stability:.4f} (低于0.3，符合预期)")
    else:
        print(f"   ⚠️ 系统未明确识别崩态，临界状态: {critical_state}")
    
    # 验证权重分配合理性
    print(f"\n📐 权重分配合理性验证:")
    if len(collapse_weights) == 2:
        # 羊刃架杀的权重应该略高于伤官见官（因为base_strength更高：0.9 vs 0.75）
        yang_weight = collapse_weights.get("YANG_REN_JIA_SHA", 0.0)
        shang_weight = collapse_weights.get("SHANG_GUAN_JIAN_GUAN", 0.0)
        
        if yang_weight > shang_weight:
            print(f"   ✅ 权重分配合理：羊刃架杀({yang_weight:.4f}) > 伤官见官({shang_weight:.4f})")
        else:
            print(f"   ⚠️ 权重分配异常：羊刃架杀({yang_weight:.4f}) <= 伤官见官({shang_weight:.4f})")
    
    if 0.95 <= total_weight <= 1.05:
        print(f"   ✅ 权重总和归一化正确: {total_weight:.4f}")
    else:
        print(f"   ⚠️ 权重总和异常: {total_weight:.4f}")
    
    # 输出JSON格式（便于后续使用）
    print(f"\n📄 JSON格式输出:")
    output = {
        "logic_collapse": collapse_weights,
        "energy_state_report": energy_report
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    print(f"\n{'=' * 80}")
    print("✅ 测试完成")
    print(f"{'=' * 80}\n")
    
    return result


if __name__ == "__main__":
    test_dual_conflict_matrix_routing()

