"""
tests/test_v6_parameterization.py
---------------------------------
[V6.0+] 算法参数化测试套件
验证 Sprint R3/R4 重构成功
"""
import sys
sys.path.insert(0, '/home/jin/bazi_predict')

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.bazi_profile import VirtualBaziProfile
from core.config_rules import (
    SCORE_SKULL_CRASH, SCORE_TREASURY_BONUS, SCORE_TREASURY_PENALTY,
    ENERGY_THRESHOLD_STRONG, ENERGY_THRESHOLD_WEAK, SCORE_GENERAL_OPEN,
    DEFAULT_CONFIG
)


def test_config_rules_import():
    """测试 config_rules 模块导入"""
    print("[TEST] config_rules 模块导入")
    assert SCORE_SKULL_CRASH == -50.0, f"Expected -50.0, got {SCORE_SKULL_CRASH}"
    assert SCORE_TREASURY_BONUS == 20.0, f"Expected 20.0, got {SCORE_TREASURY_BONUS}"
    assert SCORE_TREASURY_PENALTY == -20.0, f"Expected -20.0, got {SCORE_TREASURY_PENALTY}"
    assert ENERGY_THRESHOLD_STRONG == 3.5, f"Expected 3.5, got {ENERGY_THRESHOLD_STRONG}"
    assert ENERGY_THRESHOLD_WEAK == 2.0, f"Expected 2.0, got {ENERGY_THRESHOLD_WEAK}"
    assert SCORE_GENERAL_OPEN == 5.0, f"Expected 5.0, got {SCORE_GENERAL_OPEN}"
    print("  ✅ 通过")


def test_default_params_loading():
    """测试默认参数加载"""
    print("[TEST] 默认参数加载")
    engine = QuantumEngine()
    assert engine.skull_engine.skull_crash_score == -50.0
    assert engine.treasury_engine.treasury_bonus == 20.0
    assert engine.treasury_engine.treasury_penalty == -20.0
    print("  ✅ 通过")


def test_hot_update():
    """测试热更新功能"""
    print("[TEST] 热更新功能")
    engine = QuantumEngine()
    
    # 更新配置
    new_config = {
        'score_skull_crash': -40.0,
        'score_treasury_bonus': 30.0,
        'score_treasury_penalty': -15.0,
    }
    engine.update_config(new_config)
    
    # 验证子引擎参数已更新
    assert engine.skull_engine.skull_crash_score == -40.0, \
        f"Expected -40.0, got {engine.skull_engine.skull_crash_score}"
    assert engine.treasury_engine.treasury_bonus == 30.0, \
        f"Expected 30.0, got {engine.treasury_engine.treasury_bonus}"
    assert engine.config.get('score_skull_crash') == -40.0
    print("  ✅ 通过")


def test_skull_protocol_with_custom_params():
    """测试骷髅协议使用自定义参数"""
    print("[TEST] 骷髅协议使用自定义参数")
    engine = QuantumEngine()
    engine.update_config({'score_skull_crash': -35.0})
    
    # 构造包含丑未戌三刑的八字
    profile = VirtualBaziProfile(
        pillars={'year': '辛丑', 'month': '乙未', 'day': '己巳', 'hour': '庚午'},
        static_luck='戊戌',
        day_master='己',
        gender=1
    )
    
    # 2030年是庚戌年，触发丑未戌三刑
    ctx = engine.calculate_year_context(profile, 2030)
    
    assert ctx.score == -35.0, f"Expected -35.0, got {ctx.score}"
    assert ctx.icon == '💀', f"Expected 💀, got {ctx.icon}"
    print("  ✅ 通过")


def test_new_engine_uses_defaults():
    """测试新引擎使用默认值"""
    print("[TEST] 新引擎使用默认值")
    engine = QuantumEngine()
    
    profile = VirtualBaziProfile(
        pillars={'year': '辛丑', 'month': '乙未', 'day': '己巳', 'hour': '庚午'},
        static_luck='戊戌',
        day_master='己',
        gender=1
    )
    
    ctx = engine.calculate_year_context(profile, 2030)
    
    assert ctx.score == -50.0, f"Expected -50.0, got {ctx.score}"
    print("  ✅ 通过")


if __name__ == "__main__":
    print("=" * 60)
    print("   V6.0+ 算法参数化测试套件")
    print("=" * 60)
    
    test_config_rules_import()
    test_default_params_loading()
    test_hot_update()
    test_skull_protocol_with_custom_params()
    test_new_engine_uses_defaults()
    
    print()
    print("=" * 60)
    print("   🎉 所有测试通过！Sprint R3/R4 重构成功！")
    print("=" * 60)
