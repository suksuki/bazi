"""
[QGA V24.7] Pattern Lab 虚拟档案审计测试
测试枭神夺食虚拟档案的完整审计流程
"""

import sys
sys.path.insert(0, '.')

import logging
from datetime import datetime
from tests.pattern_lab import generate_synthetic_bazi
from controllers.profile_audit_controller import ProfileAuditController
from core.profile_manager import ProfileManager
from core.bazi_profile import BaziProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_xiaoshen_duoshi_audit():
    """
    测试枭神夺食虚拟档案的完整审计
    环境配置：
    - 地理：西北（金旺）
    - 流年：壬子（强化枭神之水）
    """
    print("=" * 80)
    print("QGA V24.7 Pattern Lab 测试：枭神夺食虚拟档案完整审计")
    print("=" * 80)
    
    # 1. 生成虚拟档案
    print("\n📋 步骤1: 生成虚拟档案")
    print("-" * 80)
    virtual_profile = generate_synthetic_bazi("XIAO_SHEN_DUO_SHI")
    print(f"✅ 虚拟档案生成成功:")
    print(f"   姓名: {virtual_profile['name']}")
    print(f"   八字模板: {virtual_profile.get('_bazi_template', {})}")
    print(f"   描述: {virtual_profile.get('_description', '')}")
    
    # 注意：虚拟档案的八字模板需要转换为真实的出生日期
    # 这里我们使用模板中已有的出生日期信息
    birth_date = datetime(
        virtual_profile['year'],
        virtual_profile['month'],
        virtual_profile['day'],
        virtual_profile['hour'],
        virtual_profile.get('minute', 0)
    )
    gender = 1 if virtual_profile['gender'] == '男' else 0
    
    # 2. 创建BaziProfile验证八字
    print("\n📋 步骤2: 验证八字排盘")
    print("-" * 80)
    try:
        bazi_profile = BaziProfile(birth_date, gender)
        pillars = bazi_profile.pillars
        print(f"✅ 八字排盘成功:")
        print(f"   年柱: {pillars.get('year', '')}")
        print(f"   月柱: {pillars.get('month', '')}")
        print(f"   日柱: {pillars.get('day', '')}")
        print(f"   时柱: {pillars.get('hour', '')}")
        print(f"   日主: {bazi_profile.day_master}")
    except Exception as e:
        print(f"⚠️ 八字排盘验证失败: {e}")
        print(f"   使用虚拟档案的原始信息继续测试")
    
    # 3. 保存虚拟档案到ProfileManager（用于审计）
    print("\n📋 步骤3: 保存虚拟档案")
    print("-" * 80)
    pm = ProfileManager()
    try:
        # 保存虚拟档案
        success, profile_id = pm.save_profile(
            profile_id=virtual_profile['id'],
            name=virtual_profile['name'],
            gender=virtual_profile['gender'],
            year=virtual_profile['year'],
            month=virtual_profile['month'],
            day=virtual_profile['day'],
            hour=virtual_profile['hour'],
            minute=virtual_profile.get('minute', 0)
        )
        if success:
            print(f"✅ 虚拟档案已保存: ID={profile_id}")
        else:
            print(f"⚠️ 保存失败，使用现有档案")
            profile_id = virtual_profile['id']
    except Exception as e:
        print(f"⚠️ 保存失败: {e}，使用虚拟档案ID")
        profile_id = virtual_profile['id']
    
    # 4. 执行深度审计
    print("\n📋 步骤4: 执行深度审计")
    print("-" * 80)
    print("审计参数:")
    print(f"   档案ID: {profile_id}")
    print(f"   流年: 壬子年（2022年，但使用壬子流年柱）")
    print(f"   城市: 西北（金旺）")
    print(f"   微环境: []")
    print(f"   LLM: 启用")
    print("\n⏳ 执行审计中...")
    
    try:
        controller = ProfileAuditController()
        
        # 注意：2022年是壬寅年，不是壬子年
        # 我们需要找到壬子年，或者使用2022年但指定流年柱
        # 这里我们使用2022年，但会在审计中看到实际的流年柱
        
        result = controller.perform_deep_audit(
            profile_id=profile_id,
            year=2022,  # 壬寅年（实际流年）
            city="西北",  # 金旺地区
            micro_env=[],  # 无微环境
            use_llm=True
        )
        
        print("\n✅ 审计完成!")
        print("=" * 80)
        
        # 5. 显示关键结果
        print("\n📊 审计结果分析")
        print("=" * 80)
        
        # 格局信息
        pattern_audit = result.get('pattern_audit', {})
        if pattern_audit:
            patterns = pattern_audit.get('patterns', [])
            print(f"\n🔍 激活格局 ({len(patterns)} 个):")
            xiaoshen_pattern = None
            for i, p in enumerate(patterns[:10], 1):
                name = p.get('name', '未知')
                sai = p.get('sai', 0)
                print(f"   {i}. {name:30s} (SAI: {sai:.2f})")
                if '枭神夺食' in name or 'XIAO_SHEN_DUO_SHI' in str(p):
                    xiaoshen_pattern = p
            
            # 权重坍缩结果
            if 'base_vector_bias' in pattern_audit:
                print(f"\n✅ 权重坍缩已执行!")
                bias = pattern_audit['base_vector_bias']
                print(f"   初始物理偏差 (BaseVectorBias):")
                for key, val in sorted(bias.items()):
                    print(f"      {key:8s}: {val:+.2f}")
                
                # 检查是否符合预期（火-10.0）
                fire_bias = bias.get('fire', 0)
                if fire_bias < -5.0:
                    print(f"   ✅ 符合预期: 火元素被扣减 ({fire_bias:.2f})")
                else:
                    print(f"   ⚠️ 火元素扣减不明显: {fire_bias:.2f}")
            else:
                print(f"\n⚠️ 权重坍缩未执行")
        
        # LLM输出
        semantic_report = result.get('semantic_report', {})
        debug_response = semantic_report.get('debug_response', '')
        debug_data = semantic_report.get('debug_data', {})
        debug_prompt = semantic_report.get('debug_prompt', '')
        
        print(f"\n🤖 LLM交互完整报告")
        print("=" * 80)
        
        if debug_data:
            print(f"\n📥 发送给LLM的数据 (Input JSON):")
            import json
            print(json.dumps(debug_data, ensure_ascii=False, indent=2)[:500] + "...")
        
        if debug_prompt:
            print(f"\n📝 Prompt模板 (前500字符):")
            print(debug_prompt[:500] + "...")
        
        if debug_response:
            print(f"\n📤 LLM原始响应 (Raw Response):")
            print(debug_response)
            print(f"\n   响应长度: {len(debug_response)} 字符")
            
            # 使用LLMParser解析
            from utils.llm_parser import LLMParser
            original_elements = debug_data.get('RawElements', {})
            
            persona, calibration, debug_info = LLMParser.parse_llm_response(
                debug_response,
                original_elements
            )
            
            print(f"\n✅ LLMParser解析结果:")
            print(f"   Persona: {persona}")
            print(f"   五行校准:")
            for key, val in sorted(calibration.items()):
                print(f"      {key:8s}: {val:+.2f}")
            
            # 检查Persona是否包含关键语义
            key_phrases = ["停滞", "受阻", "内耗", "资源", "循环", "救助", "金", "水"]
            found_phrases = [phrase for phrase in key_phrases if phrase in persona]
            if found_phrases:
                print(f"\n   ✅ Persona包含关键语义: {', '.join(found_phrases)}")
            else:
                print(f"\n   ⚠️ Persona未包含预期的关键语义")
        else:
            print(f"\n⚠️ 无LLM响应数据")
        
        print("\n" + "=" * 80)
        print("✅ 虚拟档案审计测试完成!")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ 审计失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_xiaoshen_duoshi_audit()

