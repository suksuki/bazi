"""
[QGA V25.0 Phase 2] 特征向量提取器测试
测试蒋柯栋在"北京/近水"环境下的向量指纹
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
import json


def test_jiang_kedong_vector():
    """测试蒋柯栋的特征向量提取"""
    
    print("=" * 80)
    print("🧪 测试：蒋柯栋特征向量提取（北京/近水环境）")
    print("=" * 80)
    
    # 蒋柯栋八字：丁亥 乙巳 丙午 甲午
    # 日主：丙火
    # 从儿格（食伤极旺）
    
    # 硬编码正确的八字
    chart = [
        ('丁', '亥'),  # 年柱
        ('乙', '巳'),  # 月柱
        ('丙', '午'),  # 日柱
        ('甲', '午')   # 时柱
    ]
    day_master = '丙'
    
    print(f"\n📊 四柱信息（硬编码）:")
    print(f"   年柱: {chart[0][0]}{chart[0][1]}")
    print(f"   月柱: {chart[1][0]}{chart[1][1]}")
    print(f"   日柱: {chart[2][0]}{chart[2][1]}")
    print(f"   时柱: {chart[3][0]}{chart[3][1]}")
    print(f"   日主: {day_master}")
    
    # 创建特征向量提取器
    vectorizer = FeatureVectorizer()
    
    # 提取特征向量（北京/近水环境）
    feature_vector = vectorizer.vectorize_bazi(
        chart=chart,
        day_master=day_master,
        luck_pillar=None,  # 可以后续添加
        year_pillar=None,  # 可以后续添加
        geo_info="北方/北京",
        micro_env=["近水"],
        synthesized_field=None
    )
    
    print(f"\n✅ 特征向量提取完成:")
    print(f"\n📐 五行场强分布（elemental_fields）:")
    elemental_dict = feature_vector.get("elemental_fields_dict", {})
    for elem, value in elemental_dict.items():
        print(f"   {elem:8s}: {value:.4f}")
    
    print(f"\n⚡ 应力张量（stress_tensor）: {feature_vector.get('stress_tensor', 0.0):.4f}")
    print(f"\n🌀 相位一致性（phase_coherence）: {feature_vector.get('phase_coherence', 0.0):.4f}")
    
    routing_hint = feature_vector.get("routing_hint")
    if routing_hint:
        print(f"\n🎯 路由暗示（routing_hint）: {routing_hint}")
    
    momentum_term = feature_vector.get("momentum_term", {})
    if momentum_term:
        print(f"\n🔀 动量项（momentum_term）:")
        for key, value in momentum_term.items():
            print(f"   {key:15s}: {value:.4f}")
    
    # 验证向量格式
    print(f"\n✅ 向量格式验证:")
    elemental_vector = feature_vector.get("elemental_fields", [])
    print(f"   elemental_fields (数组格式): {elemental_vector}")
    print(f"   向量长度: {len(elemental_vector)} (应为5: 金木水火土)")
    print(f"   向量和: {sum(elemental_vector):.4f} (应约等于1.0)")
    
    # 验证可预测性和可复现性
    print(f"\n🔄 可复现性测试:")
    feature_vector2 = vectorizer.vectorize_bazi(
        chart=chart,
        day_master=day_master,
        geo_info="北方/北京",
        micro_env=["近水"]
    )
    
    # 比较两次提取结果
    if abs(feature_vector["stress_tensor"] - feature_vector2["stress_tensor"]) < 0.001:
        print("   ✅ stress_tensor可复现")
    else:
        print(f"   ⚠️ stress_tensor不一致: {feature_vector['stress_tensor']:.4f} vs {feature_vector2['stress_tensor']:.4f}")
    
    if abs(feature_vector["phase_coherence"] - feature_vector2["phase_coherence"]) < 0.001:
        print("   ✅ phase_coherence可复现")
    else:
        print(f"   ⚠️ phase_coherence不一致")
    
    # 输出JSON格式（便于后续使用）
    print(f"\n📄 JSON格式输出:")
    output = {
        "elemental_fields": feature_vector["elemental_fields"],
        "stress_tensor": feature_vector["stress_tensor"],
        "phase_coherence": feature_vector["phase_coherence"],
        "routing_hint": feature_vector["routing_hint"],
        "momentum_term": feature_vector["momentum_term"]
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    print(f"\n{'=' * 80}")
    print("✅ 测试完成")
    print(f"{'=' * 80}\n")
    
    return feature_vector


if __name__ == "__main__":
    test_jiang_kedong_vector()

