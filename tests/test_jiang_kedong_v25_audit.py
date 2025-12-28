"""
[QGA V25.0 Phase 5] 蒋柯栋全息审计 - V25.0神经矩阵时代
对比V24.7（硬编码时代）与V25.0（神经矩阵时代）的判词差异
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.subjects.neural_router.execution_kernel import NeuralRouterKernel
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
from controllers.profile_audit_controller import ProfileAuditController
import json


def test_jiang_kedong_v25_full_audit():
    """对蒋柯栋执行V25.0全量审计流程"""
    
    print("=" * 80)
    print("🧬 QGA V25.0 全息审计：蒋柯栋档案")
    print("=" * 80)
    print("📋 档案信息:")
    print("   姓名: 蒋柯栋")
    print("   八字: 丁亥 乙巳 丙午 甲午")
    print("   日主: 丙火")
    print("   格局: 从儿格（食伤极旺）")
    print("   环境: 北方/北京 + 近水")
    print("   流年: 2025年")
    print("")
    
    # 方式1：通过ProfileAuditController（如果档案存在）
    controller = ProfileAuditController()
    
    try:
        # 尝试加载蒋柯栋档案
        profiles = controller.model.load_all_profiles()
        jiang_profile = None
        
        for profile in profiles:
            if "蒋" in profile.get('name', '') and "柯" in profile.get('name', ''):
                jiang_profile = profile
                break
        
        if jiang_profile:
            print(f"✅ 找到档案: {jiang_profile.get('name')} (ID: {jiang_profile.get('id')})")
            profile_id = jiang_profile.get('id')
            
            # 执行深度审计
            print("")
            print("🚀 启动V25.0神经矩阵审计...")
            print("")
            
            result = controller.perform_deep_audit(
                profile_id=profile_id,
                year=2025,
                city="北方/北京",
                micro_env=["近水"],
                use_llm=True  # 启用LLM
            )
            
            if result and 'error' not in result:
                # 注意：controller返回的结果可能不包含neural_router的结果
                # 我们需要检查是否有neural_router_metadata字段
                if 'neural_router_metadata' in result or 'logic_collapse' in result:
                    print_audit_results(result, use_controller=True)
                else:
                    print("⚠️ 控制器返回的结果不包含neural_router数据，使用直接调用方式")
                    use_direct_method = True
            else:
                print("⚠️ 控制器审计失败，使用直接调用方式")
                use_direct_method = True
        else:
            print("⚠️ 未找到蒋柯栋档案，使用硬编码八字进行直接审计")
            use_direct_method = True
            
    except Exception as e:
        print(f"⚠️ 控制器审计异常: {e}")
        print("   使用直接调用方式...")
        use_direct_method = True
    
    # 方式2：直接调用execution_kernel（使用硬编码八字）
    if 'use_direct_method' in locals() and use_direct_method:
        print("")
        print("🚀 启动V25.0神经矩阵审计（直接模式）...")
        print("")
        
        kernel = NeuralRouterKernel()
        vectorizer = FeatureVectorizer()
        
        # 硬编码蒋柯栋八字
        chart = [
            ('丁', '亥'),  # 年柱
            ('乙', '巳'),  # 月柱
            ('丙', '午'),  # 日柱
            ('甲', '午')   # 时柱
        ]
        day_master = '丙'
        
        # 提取特征向量
        feature_vector = vectorizer.vectorize_bazi(
            chart=chart,
            day_master=day_master,
            geo_info="北方/北京",
            micro_env=["近水"]
        )
        
        # 模拟激活格局（从儿格）
        active_patterns = [
            {
                "id": "CONG_ER_GE",
                "name": "从儿格",
                "weight": 0.85,
                "confidence": 0.9
            }
        ]
        
        # 执行完整审计
        result = kernel.process_bazi_profile(
            active_patterns=active_patterns,
            synthesized_field={
                "friction_index": 30.0,  # 中等应力
                "micro_env": ["近水"]
            },
            profile_name="蒋柯栋",
            day_master=day_master,
            force_vectors=feature_vector.get("elemental_fields_dict", {}),
            year=2025,
            luck_pillar=None,
            year_pillar=None,
            geo_info="北方/北京"
        )
        
        print_audit_results(result, use_controller=False)


def print_audit_results(result: dict, use_controller: bool = False):
    """打印审计结果"""
    
    print("=" * 80)
    print("📊 V25.0 神经矩阵审计结果")
    print("=" * 80)
    print("")
    
    # 1. 特征向量指纹（Phase 2）
    if "neural_router_metadata" in result:
        metadata = result["neural_router_metadata"]
        feature_vector = metadata.get("feature_vector", {})
        
        if feature_vector:
            elemental_fields = feature_vector.get("elemental_fields_dict", {})
            stress_tensor = feature_vector.get("stress_tensor", 0.0)
            phase_coherence = feature_vector.get("phase_coherence", 0.0)
            
            print("🔬 【特征向量指纹 (Phase 2)】")
            print(f"   五行场强分布:")
            for elem, value in elemental_fields.items():
                bar = "█" * int(value * 50)
                print(f"     {elem:6s}: {value:.4f} {bar}")
            print(f"   应力张量 (stress_tensor): {stress_tensor:.4f}")
            print(f"   相位一致性 (phase_coherence): {phase_coherence:.4f}")
            print("")
    
    # 2. 权重坍缩（Phase 4）
    if "logic_collapse" in result:
        print("⚖️  【逻辑权重坍缩 (Phase 4)】")
        collapse_weights = result["logic_collapse"]
        total_weight = sum(collapse_weights.values())
        
        for pattern_id, weight in sorted(collapse_weights.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 50)
            print(f"   {pattern_id:25s}: {weight:.4f} ({weight*100:.2f}%) {bar}")
        print(f"   总计: {total_weight:.4f}")
        print("")
    
    # 3. 能量状态报告（Phase 4）
    if "energy_state_report" in result:
        print("⚡ 【能量状态报告 (Phase 4)】")
        energy_report = result["energy_state_report"]
        print(f"   系统稳定性: {energy_report.get('system_stability', 0.0):.4f}")
        print(f"   临界状态: {energy_report.get('critical_state', 'N/A')}")
        print(f"   能量流向: {energy_report.get('energy_flow_direction', 'N/A')}")
        print(f"   总能量: {energy_report.get('total_energy', 0.0):.4f}")
        if 'stress_tensor' in energy_report:
            print(f"   应力张量: {energy_report['stress_tensor']:.4f}")
        if 'phase_coherence' in energy_report:
            print(f"   相位一致性: {energy_report['phase_coherence']:.4f}")
        print("")
    
    # 4. LLM生成的Persona（核心判词）
    if "persona" in result:
        print("🎯 【命运画像判词 (V25.0神经矩阵时代)】")
        persona = result["persona"]
        print(f"   {persona}")
        print("")
        
        # 分析判词质量
        print("📝 【判词质量分析】")
        quality_indicators = {
            "物理术语": ["能量", "应力", "相位", "场强", "晶格", "坍缩", "稳态", "崩态"],
            "因果链条": ["导致", "使得", "因为", "由于", "因此", "从而"],
            "量化描述": ["0.", "1.", "高", "低", "强", "弱", "%", "程度"]
        }
        
        for indicator_type, keywords in quality_indicators.items():
            count = sum(1 for kw in keywords if kw in persona)
            if count > 0:
                print(f"   ✅ {indicator_type}: 包含 {count} 个关键词")
            else:
                print(f"   ⚠️  {indicator_type}: 未检测到关键词")
        print("")
    
    # 5. 五行修正
    if "element_calibration" in result:
        print("🔧 【五行修正】")
        calibration = result["element_calibration"]
        if calibration:
            for elem, value in calibration.items():
                print(f"   {elem}: {value}")
        print("")
    
    # 6. 处理元数据
    if "neural_router_metadata" in result:
        metadata = result["neural_router_metadata"]
        print("🔧 【处理元数据】")
        print(f"   格局数: {metadata.get('pattern_count', 'N/A')}")
        print(f"   综合SAI: {metadata.get('aggregated_sai', 'N/A')}")
        print(f"   Prompt长度: {metadata.get('inline_prompt_length', 'N/A')} 字符")
        if "matrix_routing" in metadata:
            matrix_info = metadata["matrix_routing"]
            print(f"   权重数: {matrix_info.get('collapse_weights_count', 'N/A')}")
            print(f"   能量稳定性: {matrix_info.get('energy_stability', 'N/A')}")
        print("")
    
    # 7. V24.7 vs V25.0 对比分析
    print("=" * 80)
    print("🔍 【V24.7 vs V25.0 对比分析】")
    print("=" * 80)
    print("")
    print("V24.7（硬编码时代）特点:")
    print("   - 基于规则的路由，权重手动配置")
    print("   - 判词以描述现象为主")
    print("   - 缺乏能量流转的底层因果解释")
    print("")
    print("V25.0（神经矩阵时代）特点:")
    
    v25_features = []
    if "logic_collapse" in result:
        v25_features.append("✅ 自动权重坍缩：系统自发计算格局权重贡献")
    if "energy_state_report" in result:
        v25_features.append("✅ 能量状态报告：全局稳定性实时体检")
    if "neural_router_metadata" in result and metadata.get("feature_vector"):
        v25_features.append("✅ 特征向量指纹：量化物理状态")
    
    for feature in v25_features:
        print(f"   {feature}")
    
    if "persona" in result:
        persona = result["persona"]
        if any(kw in persona for kw in ["能量", "应力", "相位", "场强"]):
            print("   ✅ 判词升级：从描述现象到解释能量流转的底层因果")
        else:
            print("   ⚠️  判词风格：仍以描述为主，可能未充分体现物理逻辑")
    print("")
    
    # 输出完整JSON（便于后续分析）
    print("=" * 80)
    print("📄 【完整JSON输出】")
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("")
    
    print("=" * 80)
    print("✅ V25.0 全息审计完成")
    print("=" * 80)


if __name__ == "__main__":
    print("🧬 QGA V25.0 Phase 5: 蒋柯栋全息审计测试")
    print("   此测试将运行完整的神经矩阵路由流程")
    print("   包括：特征向量提取 → 逻辑公理匹配 → LLM生成 → 权重坍缩 → 能量状态分析")
    print("")
    
    test_jiang_kedong_v25_full_audit()

