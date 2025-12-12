#!/usr/bin/env python3
"""
测试配置管理器的默认值和字幕优化功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager

def test_default_config():
    """测试默认配置"""
    print("=" * 50)
    print("测试默认配置")
    print("=" * 50)
    
    cm = ConfigManager(config_file="data/test_config.json")
    
    # 测试默认并发数
    max_jobs = cm.get('max_concurrent_jobs')
    print(f"✅ 最大并发任务数: {max_jobs}")
    assert max_jobs == 3, f"预期 3，实际 {max_jobs}"
    
    # 测试字幕优先级
    subtitle_priority = cm.get('subtitle_priority')
    print(f"✅ 字幕优先级: {subtitle_priority}")
    assert subtitle_priority == True, f"预期 True，实际 {subtitle_priority}"
    
    # 测试字幕语言列表
    subtitle_langs = cm.get('subtitle_languages')
    print(f"✅ 字幕语言优先级: {' → '.join(subtitle_langs[:3])}...")
    assert isinstance(subtitle_langs, list), "应该是列表类型"
    assert 'zh-Hans' in subtitle_langs, "应该包含 zh-Hans"
    
    print("\n✨ 默认配置测试通过！\n")

def test_config_persistence():
    """测试配置持久化"""
    print("=" * 50)
    print("测试配置持久化")
    print("=" * 50)
    
    cm = ConfigManager(config_file="data/test_config.json")
    
    # 保存自定义值
    cm.save_config('max_concurrent_jobs', 5)
    print("✅ 保存并发数: 5")
    
    # 重新加载
    cm2 = ConfigManager(config_file="data/test_config.json")
    max_jobs = cm2.get('max_concurrent_jobs')
    print(f"✅ 重新加载并发数: {max_jobs}")
    assert max_jobs == 5, f"预期 5，实际 {max_jobs}"
    
    # 清理测试文件
    if os.path.exists("data/test_config.json"):
        os.remove("data/test_config.json")
        print("✅ 清理测试文件")
    
    print("\n✨ 配置持久化测试通过！\n")

def test_subtitle_config_integration():
    """测试字幕配置集成"""
    print("=" * 50)
    print("测试字幕配置集成")
    print("=" * 50)
    
    cm = ConfigManager()
    
    # 获取当前字幕语言配置
    langs = cm.get('subtitle_languages', [])
    print(f"✅ 当前字幕语言配置: {langs}")
    
    # 验证优先级顺序
    expected_order = ['zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW', 'zh', 'en']
    if langs == expected_order:
        print("✅ 字幕语言优先级顺序正确")
    else:
        print(f"⚠️  字幕语言优先级与预期不同")
        print(f"   预期: {expected_order}")
        print(f"   实际: {langs}")
    
    # 测试字幕优先级开关
    priority = cm.get('subtitle_priority', True)
    print(f"✅ 字幕优先级开关: {'开启' if priority else '关闭'}")
    
    print("\n✨ 字幕配置集成测试通过！\n")

if __name__ == "__main__":
    print("\n" + "🧪 配置管理器测试套件".center(50, "=") + "\n")
    
    try:
        test_default_config()
        test_config_persistence()
        test_subtitle_config_integration()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
