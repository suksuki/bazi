"""
[QGA V25.0 Phase 4] 神经网络路由集成测试
真正连接LLM，测试完整的流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.subjects.neural_router.execution_kernel import NeuralRouterKernel
import json


def test_neural_router_with_llm():
    """测试完整的神经网络路由流程（连接LLM）"""
    
    print("=" * 80)
    print("🧪 集成测试：神经网络路由完整流程（LLM连接）")
    print("=" * 80)
    print("⚠️  注意：此测试需要LLM服务运行（例如Ollama）")
    print("")
    
    # 创建执行内核
    kernel = NeuralRouterKernel()
    
    # 模拟激活格局（伤官见官 + 羊刃架杀）
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
    
    # 模拟合成场强
    synthesized_field = {
        "friction_index": 82.0,  # 高应力
        "micro_env": ["近水"]
    }
    
    # 模拟五行场强
    force_vectors = {
        "metal": 0.25,
        "wood": 0.20,
        "water": 0.15,
        "fire": 0.30,
        "earth": 0.10
    }
    
    print("📋 测试参数:")
    print(f"   档案名: 双重矛盾测试档案")
    print(f"   日主: 丙")
    print(f"   激活格局数: {len(active_patterns)}")
    print(f"   地理信息: 北方/北京")
    print(f"   流年: 2025")
    print("")
    
    try:
        # 调用完整的处理流程（这会真正调用LLM）
        result = kernel.process_bazi_profile(
            active_patterns=active_patterns,
            synthesized_field=synthesized_field,
            profile_name="双重矛盾测试档案",
            day_master="丙",
            force_vectors=force_vectors,
            year=2025,
            luck_pillar="甲子",
            year_pillar="乙巳",
            geo_info="北方/北京"
        )
        
        print("✅ LLM处理完成!")
        print("")
        
        # 检查返回结果
        print("📊 返回结果结构:")
        print(f"   - persona: {'✅' if 'persona' in result else '❌'}")
        print(f"   - element_calibration: {'✅' if 'element_calibration' in result else '❌'}")
        print(f"   - logic_collapse: {'✅' if 'logic_collapse' in result else '❌'}")
        print(f"   - energy_state_report: {'✅' if 'energy_state_report' in result else '❌'}")
        print(f"   - neural_router_metadata: {'✅' if 'neural_router_metadata' in result else '❌'}")
        print("")
        
        # 显示权重坍缩结果
        if "logic_collapse" in result:
            print("📈 权重坍缩结果:")
            collapse_weights = result["logic_collapse"]
            total_weight = sum(collapse_weights.values())
            for pattern_id, weight in collapse_weights.items():
                print(f"   {pattern_id:25s}: {weight:.4f} ({weight*100:.2f}%)")
            print(f"   总计: {total_weight:.4f}")
            print("")
        
        # 显示能量状态报告
        if "energy_state_report" in result:
            print("⚡ 能量状态报告:")
            energy_report = result["energy_state_report"]
            print(f"   系统稳定性: {energy_report.get('system_stability', 'N/A')}")
            print(f"   临界状态: {energy_report.get('critical_state', 'N/A')}")
            print(f"   能量流向: {energy_report.get('energy_flow_direction', 'N/A')}")
            print("")
        
        # 显示persona（如果LLM成功生成）
        if "persona" in result and result["persona"]:
            print("📝 LLM生成的Persona:")
            persona = result["persona"]
            # 只显示前200字符
            print(f"   {persona[:200]}...")
            print("")
        
        # 显示元数据
        if "neural_router_metadata" in result:
            metadata = result["neural_router_metadata"]
            print("🔧 处理元数据:")
            print(f"   格局数: {metadata.get('pattern_count', 'N/A')}")
            print(f"   综合SAI: {metadata.get('aggregated_sai', 'N/A')}")
            print(f"   Prompt长度: {metadata.get('inline_prompt_length', 'N/A')} 字符")
            if "matrix_routing" in metadata:
                matrix_info = metadata["matrix_routing"]
                print(f"   权重数: {matrix_info.get('collapse_weights_count', 'N/A')}")
                print(f"   能量稳定性: {matrix_info.get('energy_stability', 'N/A'):.4f}")
            print("")
        
        # 输出完整JSON（便于调试）
        print("📄 完整JSON输出（前500字符）:")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        print(result_json[:500] + "...")
        print("")
        
        print("=" * 80)
        print("✅ 集成测试完成")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("")
        print("💡 可能的原因:")
        print("   1. LLM服务未运行（需要启动Ollama等服务）")
        print("   2. 配置文件中的LLM模型名称不正确")
        print("   3. 网络连接问题（如果使用远程LLM）")
        return None


if __name__ == "__main__":
    print("⚠️  警告：此测试会真正调用LLM API，需要LLM服务运行")
    print("   如果只想测试逻辑层，请运行 test_matrix_router_dual_conflict.py")
    print("")
    
    import sys
    response = input("是否继续？(y/n): ").strip().lower()
    if response == 'y':
        test_neural_router_with_llm()
    else:
        print("测试已取消")

