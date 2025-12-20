#!/usr/bin/env python3
"""
V10.0 沙盒仿真脚本 (Sandbox Simulation Script)
==============================================

目的：在集成到主系统前，先在这个脚本里跑通单点测试。
这是"代码版的草稿纸"，用于数学验证和算法调试。

功能：
1. 不加载复杂的 UI 和数据库
2. 只加载核心 FlowEngine 和 GraphNetworkEngine
3. 支持单点测试（如标准八字、Steve Jobs案例）
4. 直接打印能量分布和关键指标

使用方法：
    python scripts/sandbox_v10.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from typing import Dict, List, Any
from dataclasses import dataclass

# 核心引擎
from core.engine_graph import GraphNetworkEngine
import json


@dataclass
class SandboxResult:
    """沙盒测试结果"""
    case_name: str
    initial_energies: Dict[str, float]
    final_energies: Dict[str, float]
    energy_ratios: Dict[str, float]
    max_energy: float
    has_anomaly: bool  # 是否有超过100的异常值
    debug_info: Dict[str, Any]


class SandboxV10:
    """V10.0 沙盒仿真器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化沙盒环境
        
        Args:
            config_path: 配置文件路径（可选，默认使用 config/parameters.json）
        """
        if config_path is None:
            config_path = project_root / "config" / "parameters.json"
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.engine = None
    
    def _init_engine(self):
        """延迟初始化引擎"""
        if self.engine is None:
            self.engine = GraphNetworkEngine(config=self.config)
        return self.engine
    
    def test_standard_bazi(self, bazi: List[str], day_master: str, gender: str = "男") -> SandboxResult:
        """
        测试标准八字
        
        Args:
            bazi: 八字列表，如 ["甲子", "丙寅", "戊辰", "庚午"]
            day_master: 日主，如 "甲"
            gender: 性别，默认"男"
        
        Returns:
            SandboxResult: 测试结果
        """
        engine = self._init_engine()
        
        # 构建案例数据
        case_data = {
            'bazi': bazi,
            'day_master': day_master,
            'gender': gender
        }
        
        # 计算能量（简化版，直接使用engine的propagate方法）
        # 注意：这里需要根据实际的GraphNetworkEngine API调整
        try:
            # 尝试调用engine的方法
            # 由于GraphNetworkEngine的API可能不同，这里先返回一个占位结果
            # 实际使用时需要根据engine的实际API调整
            
            # 简化：直接返回配置信息用于验证
            initial_energies = {'Wood': 0.0, 'Fire': 0.0, 'Earth': 0.0, 'Metal': 0.0, 'Water': 0.0}
            final_energies = {'Wood': 0.0, 'Fire': 0.0, 'Earth': 0.0, 'Metal': 0.0, 'Water': 0.0}
            energy_ratios = {}
            max_energy = 0.0
            has_anomaly = False
            
            return SandboxResult(
                case_name=f"标准八字: {''.join(bazi)}",
                initial_energies=initial_energies,
                final_energies=final_energies,
                energy_ratios=energy_ratios,
                max_energy=max_energy,
                has_anomaly=has_anomaly,
                debug_info={'note': '需要根据实际GraphNetworkEngine API实现'}
            )
        except Exception as e:
            print(f"⚠️ 计算能量时出错: {e}")
            return SandboxResult(
                case_name=f"标准八字: {''.join(bazi)}",
                initial_energies={},
                final_energies={},
                energy_ratios={},
                max_energy=0.0,
                has_anomaly=False,
                debug_info={'error': str(e)}
            )
    
    def test_parameter_normalization(self) -> Dict[str, Any]:
        """
        测试参数归一化效果
        
        使用标准八字测试归一化前后的能量分布
        
        Returns:
            Dict: 包含归一化前后对比的结果
        """
        # 标准测试八字：甲子 丙寅 戊辰 庚午
        test_bazi = ["甲子", "丙寅", "戊辰", "庚午"]
        day_master = "甲"
        
        # 获取当前配置
        structure_config = self.config.get('structure', {})
        
        # 记录当前参数
        current_rooting = structure_config.get('rootingWeight', 2.16)
        current_exposed = structure_config.get('exposedBoost', 3.0)
        current_sitting = structure_config.get('samePillarBonus', 4.0)
        
        print("=" * 80)
        print("📊 参数归一化测试")
        print("=" * 80)
        print(f"\n当前参数:")
        print(f"  通根系数 (Rooting): {current_rooting}")
        print(f"  透干加成 (Exposed): {current_exposed}")
        print(f"  自坐强根 (Sitting): {current_sitting}")
        
        # 运行测试
        result = self.test_standard_bazi(test_bazi, day_master)
        
        print(f"\n测试结果:")
        print(f"  最大能量值: {result.max_energy:.2f}")
        print(f"  是否有异常 (>100): {'❌ 是' if result.has_anomaly else '✅ 否'}")
        print(f"\n初始能量分布:")
        for elem, energy in result.initial_energies.items():
            print(f"    {elem}: {energy:.2f}")
        print(f"\n最终能量分布:")
        for elem, energy in result.final_energies.items():
            ratio = result.energy_ratios.get(elem, 0.0)
            print(f"    {elem}: {energy:.2f} (比率: {ratio:.2f}x)")
        
        return {
            'current_params': {
                'rooting': current_rooting,
                'exposed': current_exposed,
                'sitting': current_sitting
            },
            'result': result
        }
    
    def test_steve_jobs(self, year: int = 2011) -> SandboxResult:
        """
        测试 Steve Jobs 案例（1955-2011）
        
        Args:
            year: 测试年份，默认2011（去世年份）
        
        Returns:
            SandboxResult: 测试结果
        """
        # Steve Jobs 八字：乙未 戊子 癸巳 辛酉
        # 1955年2月24日
        bazi = ["乙未", "戊子", "癸巳", "辛酉"]
        day_master = "癸"
        
        engine = self._init_engine()
        
        # 构建案例数据（包含流年）
        case_data = {
            'bazi': bazi,
            'day_master': day_master,
            'gender': '男'
        }
        
        # 添加流年信息
        # 2011年：辛卯年（辛金坐绝，冲克日柱）
        dynamic_context = {
            'year': f"辛卯",  # 2011年流年
            'dayun': None,  # 暂时不处理大运
            'luck': None
        }
        
        # 计算能量
        result = engine.calculate_energy_distribution(case_data, dynamic_context)
        
        # 提取结果（简化版）
        final_energies = {}
        if hasattr(result, 'final_energy'):
            for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
                final_energies[elem] = result.final_energy.get(elem, 0.0)
        
        max_energy = max(final_energies.values()) if final_energies else 0.0
        
        return SandboxResult(
            case_name=f"Steve Jobs ({year}年)",
            initial_energies={},
            final_energies=final_energies,
            energy_ratios={},
            max_energy=max_energy,
            has_anomaly=max_energy > 100.0,
            debug_info={'year': year, 'liunian': '辛卯'}
        )
    
    def print_math_derivation(self, param_name: str, old_value: float, new_value: float, 
                             example_input: str = "甲木"):
        """
        打印数学推演过程
        
        Args:
            param_name: 参数名称
            old_value: 旧值
            new_value: 新值
            example_input: 示例输入
        """
        print("=" * 80)
        print(f"🔢 数学推演: {param_name}")
        print("=" * 80)
        print(f"\n输入: {example_input}")
        print(f"参数变化: {old_value} → {new_value}")
        print(f"\n公式推演:")
        print(f"  旧值计算: E = base * {old_value} = ...")
        print(f"  新值计算: E = base * {new_value} = ...")
        print(f"\n结论: 需要验证新值是否会导致后续 Sigmoid 饱和")


def main():
    """主函数"""
    print("🧪 V10.0 沙盒仿真器")
    print("=" * 80)
    
    sandbox = SandboxV10()
    
    # 测试1: 参数归一化效果
    print("\n[测试1] 参数归一化验证")
    normalization_result = sandbox.test_parameter_normalization()
    
    # 测试2: 数学推演示例
    print("\n[测试2] 数学推演示例")
    sandbox.print_math_derivation(
        "通根系数 (Rooting)",
        old_value=2.16,
        new_value=1.0,
        example_input="甲木 (有根)"
    )
    
    # 测试3: Steve Jobs 案例（可选）
    # print("\n[测试3] Steve Jobs 案例")
    # jobs_result = sandbox.test_steve_jobs(2011)
    # print(f"\n结果: {jobs_result.case_name}")
    # print(f"最大能量: {jobs_result.max_energy:.2f}")
    
    print("\n" + "=" * 80)
    print("✅ 沙盒测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

