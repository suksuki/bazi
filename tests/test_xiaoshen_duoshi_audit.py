"""
[QGA V24.7] 枭神夺食专项审计测试
测试目标：验证枭神夺食格局在北方+近水环境下的物理逻辑
"""

import sys
sys.path.insert(0, '.')

import logging
from tests.pattern_lab import generate_synthetic_bazi
from controllers.profile_audit_controller import ProfileAuditController
from core.profile_manager import ProfileManager

logging.basicConfig(level=logging.WARNING)  # 只显示警告和错误

print("=" * 80)
print("QGA V24.7 枭神夺食专项审计测试")
print("=" * 80)

# 1. 生成硬编码虚拟档案
print("\n📋 步骤1: 生成枭神夺食硬编码虚拟档案")
print("-" * 80)

try:
    virtual_profile = generate_synthetic_bazi("XIAO_SHEN_DUO_SHI", use_hardcoded=True)
    print(f"✅ 虚拟档案生成成功:")
    print(f"   名称: {virtual_profile['name']}")
    print(f"   硬编码干支: {virtual_profile.get('_hardcoded_pillars', {})}")
    print(f"   日主: {virtual_profile.get('_day_master', '')}")
    print(f"   描述: {virtual_profile.get('_description', '')}")
except Exception as e:
    print(f"❌ 生成失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 2. 保存虚拟档案
print("\n📋 步骤2: 保存虚拟档案")
print("-" * 80)

pm = ProfileManager()
try:
    # 保存虚拟档案（包含硬编码信息）
    success, profile_id = pm.save_profile(
        profile_id=virtual_profile['id'],
        name=virtual_profile['name'],
        gender=virtual_profile['gender'],
        year=virtual_profile['year'],
        month=virtual_profile['month'],
        day=virtual_profile['day'],
        hour=virtual_profile['hour']
    )
    
    if success:
        print(f"✅ 虚拟档案已保存: ID={profile_id}")
        
        # 手动添加硬编码字段到保存的档案（ProfileManager不保存这些字段，需要手动处理）
        # 注意：这里我们直接使用虚拟档案的ID，后续审计时会从虚拟档案中读取硬编码信息
        print(f"   ⚠️ 注意: ProfileManager不保存硬编码字段，审计时将使用虚拟档案数据")
    else:
        print(f"⚠️ 保存失败，使用虚拟档案ID")
        profile_id = virtual_profile['id']
except Exception as e:
    print(f"⚠️ 保存失败: {e}，使用虚拟档案ID")
    profile_id = virtual_profile['id']

# 3. 执行深度审计（北方+近水环境）
print("\n📋 步骤3: 执行深度审计")
print("-" * 80)
print("审计参数:")
print(f"   档案: {virtual_profile['name']} (ID: {profile_id})")
print(f"   流年: 2025年 (乙巳)")
print(f"   城市: 北方 (水旺，强化枭神木的杀伤力)")
print(f"   微环境: 近水")
print(f"   LLM: 启用")

controller = ProfileAuditController()

# 注意：由于ProfileManager不保存硬编码字段，我们需要手动将虚拟档案数据注入到controller
# 或者修改controller使其能够从虚拟档案中读取硬编码信息
# 这里我们使用一个临时方案：直接修改controller的model来注入虚拟档案数据

# 临时方案：直接使用虚拟档案数据创建审计结果
# 但更好的方案是修改controller支持虚拟档案
# 我们先尝试直接调用，看看是否能工作

try:
    result = controller.perform_deep_audit(
        profile_id=profile_id,
        year=2025,  # 乙巳年
        city="北方",  # 水旺地区
        micro_env=["近水"],  # 近水微环境
        use_llm=True
    )
    
    if 'error' in result:
        print(f"\n❌ 审计失败: {result['error']}")
        print(f"   可能原因: ProfileManager保存的档案缺少硬编码字段")
        print(f"   解决方案: 需要修改ProfileAuditController支持虚拟档案")
        exit(1)
    
    print("✅ 审计完成!")
    
except Exception as e:
    print(f"\n❌ 审计异常: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. 分析结果
print("\n" + "=" * 80)
print("📊 审计结果分析")
print("=" * 80)

# 4.1 BaseVectorBias分析
pattern_audit = result.get('pattern_audit', {})
if 'base_vector_bias' in pattern_audit:
    print("\n✅ [BaseVectorBias] 初始物理偏差:")
    print("-" * 80)
    bias = pattern_audit['base_vector_bias']
    geo_context = pattern_audit.get('geo_context', '')
    
    print(f"   地理环境: {geo_context}")
    print(f"\n   元素偏差:")
    element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
    for en_name, cn_name in element_map.items():
        val = bias.get(en_name, 0.0)
        if abs(val) > 0.1:  # 只显示显著变化
            sign = "+" if val >= 0 else ""
            print(f"     {cn_name:2s} ({en_name:6s}): {sign}{val:7.2f}")
    
    # 验证是否符合预期
    print(f"\n   ✅ 预期检查:")
    fire_bias = bias.get('fire', 0)
    earth_bias = bias.get('earth', 0)
    water_bias = bias.get('water', 0)
    wood_bias = bias.get('wood', 0)
    
    # 枭神夺食预期：
    # - 火（食神被夺）应该被扣减（-10.0或更少，北方/近水环境可能-15.0）
    # - 土（食神）可能被扣减或需要通关
    # - 水（偏印/枭）在北方/近水环境下增强
    # - 木（枭）可能增强
    
    if fire_bias < -5.0:
        print(f"     ✅ 火元素扣减符合预期: {fire_bias:.2f} (食神被夺，表达受阻)")
    else:
        print(f"     ⚠️ 火元素扣减不明显: {fire_bias:.2f} (预期 < -5.0)")
    
    if earth_bias < 0 or earth_bias < 5.0:
        print(f"     ✅ 土元素变化符合预期: {earth_bias:.2f} (食神场强可能下降)")
    else:
        print(f"     ⚠️ 土元素变化异常: {earth_bias:.2f}")
    
    if water_bias > 0 or wood_bias > 0:
        print(f"     ✅ 水/木元素增强符合预期: 水={water_bias:.2f}, 木={wood_bias:.2f} (北方/近水环境强化枭神)")
    else:
        print(f"     ⚠️ 水/木元素增强不明显: 水={water_bias:.2f}, 木={wood_bias:.2f}")
else:
    print("\n⚠️ [BaseVectorBias] 未计算")
    print("   可能原因: 格局引擎未匹配或权重坍缩未执行")

# 4.2 激活格局分析
if 'patterns' in pattern_audit:
    patterns = pattern_audit['patterns']
    xiaoshen_patterns = [p for p in patterns if '枭神' in p.get('name', '') or '夺食' in p.get('name', '') or 'XIAO_SHEN' in str(p)]
    
    print(f"\n✅ [激活格局] 共{len(patterns)}个格局")
    if xiaoshen_patterns:
        print(f"   枭神夺食相关格局: {len(xiaoshen_patterns)}个")
        for p in xiaoshen_patterns[:3]:
            print(f"     - {p.get('name', '')} (SAI: {p.get('sai', 0):.2f}, Strength: {p.get('Strength', 0):.2f})")
    else:
        print(f"   ⚠️ 未检测到枭神夺食格局（可能被其他格局覆盖）")
        print(f"   前3个激活格局:")
        for p in patterns[:3]:
            print(f"     - {p.get('name', '')} (SAI: {p.get('sai', 0):.2f})")

# 4.3 LLM语义合成分析
semantic_report = result.get('semantic_report', {})
persona = semantic_report.get('persona', '')
debug_response = semantic_report.get('debug_response', '')

if persona:
    print(f"\n✅ [LLM语义合成] 画像:")
    print("-" * 80)
    print(f"   {persona}")
    
    # 检查关键语义
    key_phrases = [
        "受阻", "停滞", "无法释放", "供给", "截断", "才华", "精神", "内耗", 
        "资源", "循环", "封锁", "拦截", "表达", "欲望", "水生木", "甲木"
    ]
    found_phrases = [phrase for phrase in key_phrases if phrase in persona]
    
    print(f"\n   ✅ 关键语义检查:")
    if found_phrases:
        print(f"     ✅ 包含关键语义: {', '.join(found_phrases)}")
    else:
        print(f"     ⚠️ 未包含预期的关键语义")
    
    # 检查是否符合"水生木（枭）增强了拦截，导致火（日主）的表达欲望被甲木彻底封锁"
    if any(phrase in persona for phrase in ["水生木", "甲木", "拦截", "封锁"]) and \
       any(phrase in persona for phrase in ["表达", "欲望", "火", "日主"]):
        print(f"     ✅ 核心判词验证通过：体现了'水生木（枭）增强了拦截，导致火（日主）的表达欲望被甲木彻底封锁'")
    else:
        print(f"     ⚠️ 核心判词验证未完全通过")
    
    if debug_response:
        print(f"\n   📤 LLM原始响应（前200字符）:")
        print(f"   {debug_response[:200]}...")
else:
    print(f"\n⚠️ [LLM语义合成] 未生成画像")

# 4.4 五行校准分析
llm_calibration = result.get('llm_calibration', {})
if llm_calibration:
    print(f"\n✅ [五行校准] LLM微调偏移:")
    print("-" * 80)
    element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
    for en_name, cn_name in element_map.items():
        val = llm_calibration.get(en_name, 0.0)
        if abs(val) > 0.1:  # 只显示显著变化
            sign = "+" if val >= 0 else ""
            print(f"     {cn_name:2s} ({en_name:6s}): {sign}{val:7.2f}")

print("\n" + "=" * 80)
print("✅ 枭神夺食专项审计测试完成!")
print("=" * 80)

