#!/usr/bin/env python3
"""
V10.3 Cursor Agent Loop - 真正的智能体工作流
============================================

实现完整的"观察-思考-行动"循环，让Cursor能够：
1. 读取调优结果和日志
2. 根据结果自动修改代码
3. 继续执行优化

这个脚本会：
- 运行诊断和优化
- 将结果写入结构化文件（供Cursor读取）
- 在终端输出清晰的日志（供Cursor分析）
- 如果出现问题，生成明确的错误报告

使用方法：
    python3 scripts/v10_3_cursor_agent_loop.py --mode auto
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.v10_2_mcp_server import MCPTuningServer
from scripts.v10_2_auto_driver import AutoDriver

logger = logging.getLogger(__name__)

# 确保日志目录存在
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'cursor_agent_loop.log'),
        logging.StreamHandler()
    ]
)


class CursorAgentLoop:
    """
    Cursor智能体工作流
    
    实现完整的"观察-思考-行动"循环，让Cursor能够自动优化代码
    """
    
    def __init__(self):
        self.server = MCPTuningServer()
        self.driver = AutoDriver()
        self.context_file = project_root / "config" / "cursor_context.json"
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        
    def save_context_for_cursor(self, 
                                stage: str,
                                diagnosis: Dict[str, Any],
                                action_taken: Optional[str] = None,
                                code_changes: Optional[list] = None,
                                next_action: Optional[str] = None) -> None:
        """
        保存上下文供Cursor读取
        
        Args:
            stage: 当前阶段（"observation", "thinking", "action", "result"）
            diagnosis: 诊断结果
            action_taken: 已执行的操作
            code_changes: 代码变更列表
            next_action: 下一步建议
        """
        context = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'diagnosis': {
                'match_rate': diagnosis.get('current_match_rate', 0.0),
                'total_cases': diagnosis.get('total_cases', 0),
                'matched_cases': diagnosis.get('matched_cases', 0),
                'main_issues': diagnosis.get('main_issues', [])[:5],  # 只保留前5个
                'recommendations': diagnosis.get('recommendations', [])[:3]  # 只保留前3个
            },
            'action_taken': action_taken,
            'code_changes': code_changes or [],
            'next_action': next_action,
            'status': 'needs_attention' if stage == 'result' and diagnosis.get('current_match_rate', 0) < 65.0 else 'ok'
        }
        
        # 保存到文件
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📝 上下文已保存到: {self.context_file}")
        
        # 同时在终端输出结构化信息（供Cursor读取）
        print("\n" + "="*80)
        print("📋 [CURSOR CONTEXT] 上下文信息（供Cursor读取）")
        print("="*80)
        print(json.dumps(context, ensure_ascii=False, indent=2))
        print("="*80 + "\n")
    
    def run_observation(self) -> Dict[str, Any]:
        """
        观察阶段：运行诊断
        
        Returns:
            诊断报告
        """
        logger.info("="*80)
        logger.info("🔍 [观察] 运行物理诊断...")
        logger.info("="*80)
        
        diagnosis = self.server.run_physics_diagnosis()
        
        # 保存上下文
        self.save_context_for_cursor(
            stage='observation',
            diagnosis=diagnosis,
            next_action='analyze_diagnosis'
        )
        
        return diagnosis
    
    def run_thinking(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        思考阶段：分析问题，决定行动
        
        Args:
            diagnosis: 诊断报告
            
        Returns:
            决策结果
        """
        logger.info("="*80)
        logger.info("💭 [思考] 分析问题，制定策略...")
        logger.info("="*80)
        
        match_rate = diagnosis.get('current_match_rate', 0.0)
        main_issues = diagnosis.get('main_issues', [])
        
        # 分析主要问题
        decision = {
            'action_type': None,
            'reason': None,
            'code_changes_needed': []
        }
        
        # 判断是否需要逻辑重构
        if match_rate < 55.0:
            # 匹配率太低，需要逻辑重构
            decision['action_type'] = 'logic_refactoring'
            decision['reason'] = f'匹配率 {match_rate:.1f}% 过低，需要逻辑重构而非参数调优'
            
            # 分析具体问题，生成代码变更建议
            for issue in main_issues[:3]:  # 只处理前3个问题
                pattern = issue.get('pattern', '')
                if 'Special_Strong → Balanced' in pattern:
                    decision['code_changes_needed'].append({
                        'file': 'core/engine_graph.py',
                        'function': 'calculate_strength_score',
                        'change': '降低Special_Strong判定阈值或增强判定逻辑',
                        'reason': f'有{issue.get("count", 0)}个案例被误判为Balanced'
                    })
                elif 'Weak → Strong' in pattern or 'Strong → Weak' in pattern:
                    decision['code_changes_needed'].append({
                        'file': 'core/engine_graph.py',
                        'function': '_calculate_node_base_energy',
                        'change': '优化通根识别逻辑或提高主气根加成',
                        'reason': f'有{issue.get("count", 0)}个案例Strong↔Weak互判错误'
                    })
        
        elif match_rate < 65.0:
            # 匹配率中等，可以尝试参数优化
            decision['action_type'] = 'parameter_tuning'
            decision['reason'] = f'匹配率 {match_rate:.1f}% 接近目标，尝试参数优化'
        else:
            # 已达到目标
            decision['action_type'] = 'done'
            decision['reason'] = f'匹配率 {match_rate:.1f}% 已达到目标，无需优化'
        
        # 保存上下文
        self.save_context_for_cursor(
            stage='thinking',
            diagnosis=diagnosis,
            next_action=decision['action_type'],
            code_changes=decision.get('code_changes_needed', [])
        )
        
        logger.info(f"💡 决策: {decision['action_type']} - {decision['reason']}")
        if decision.get('code_changes_needed'):
            logger.info("📝 建议的代码变更:")
            for change in decision['code_changes_needed']:
                logger.info(f"   - {change['file']}: {change['change']}")
        
        return decision
    
    def run_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        行动阶段：执行优化或代码修改
        
        Args:
            decision: 决策结果
            
        Returns:
            执行结果
        """
        logger.info("="*80)
        logger.info(f"🚀 [行动] 执行: {decision['action_type']}")
        logger.info("="*80)
        
        action_result = {
            'action_type': decision['action_type'],
            'success': False,
            'message': None,
            'code_changes_made': []
        }
        
        if decision['action_type'] == 'logic_refactoring':
            # 逻辑重构：需要Cursor修改代码
            logger.info("⚠️  需要逻辑重构，但代码修改需要Cursor执行")
            logger.info("📝 已生成代码变更建议，请Cursor根据建议修改代码")
            
            action_result['success'] = True
            action_result['message'] = '需要Cursor修改代码'
            action_result['code_changes_made'] = decision.get('code_changes_needed', [])
            
            # 保存上下文，明确告诉Cursor需要做什么
            diagnosis = self.server.run_physics_diagnosis()
            self.save_context_for_cursor(
                stage='action',
                diagnosis=diagnosis,
                action_taken='logic_refactoring_requested',
                code_changes=decision.get('code_changes_needed', []),
                next_action='modify_code'
            )
            
        elif decision['action_type'] == 'parameter_tuning':
            # 参数优化：可以自动执行
            logger.info("🔧 执行参数优化...")
            try:
                result = self.driver.run_full_auto(
                    phase1_trials=50,
                    phase2_trials=50,
                    phase3_trials=50
                )
                
                # 重新诊断
                diagnosis = self.server.run_physics_diagnosis()
                
                action_result['success'] = True
                action_result['message'] = f'参数优化完成，新匹配率: {diagnosis["current_match_rate"]:.1f}%'
                
                # 保存上下文
                self.save_context_for_cursor(
                    stage='result',
                    diagnosis=diagnosis,
                    action_taken='parameter_tuning_completed',
                    next_action='check_result'
                )
                
            except Exception as e:
                logger.error(f"❌ 参数优化失败: {e}")
                action_result['success'] = False
                action_result['message'] = f'优化失败: {str(e)}'
                
                # 保存错误上下文
                diagnosis = self.server.run_physics_diagnosis()
                self.save_context_for_cursor(
                    stage='error',
                    diagnosis=diagnosis,
                    action_taken='parameter_tuning_failed',
                    next_action='fix_error'
                )
        
        elif decision['action_type'] == 'done':
            action_result['success'] = True
            action_result['message'] = '已达到目标，无需优化'
        
        return action_result
    
    def run_full_loop(self) -> Dict[str, Any]:
        """
        运行完整的智能体循环
        
        Returns:
            完整结果
        """
        logger.info("="*80)
        logger.info("🤖 Cursor智能体工作流启动")
        logger.info("="*80)
        
        results = {
            'observation': None,
            'thinking': None,
            'action': None,
            'final': None
        }
        
        try:
            # 1. 观察
            diagnosis = self.run_observation()
            results['observation'] = diagnosis
            
            # 2. 思考
            decision = self.run_thinking(diagnosis)
            results['thinking'] = decision
            
            # 3. 行动
            if decision['action_type'] != 'done':
                action_result = self.run_action(decision)
                results['action'] = action_result
                
                # 4. 最终结果
                final_diagnosis = self.server.run_physics_diagnosis()
                results['final'] = {
                    'match_rate': final_diagnosis['current_match_rate'],
                    'status': 'success' if action_result['success'] else 'error',
                    'needs_cursor_attention': decision['action_type'] == 'logic_refactoring'
                }
                
                # 保存最终上下文
                self.save_context_for_cursor(
                    stage='result',
                    diagnosis=final_diagnosis,
                    action_taken=action_result.get('action_type', 'unknown'),
                    code_changes=action_result.get('code_changes_made', []),
                    next_action='review_result' if results['final']['needs_cursor_attention'] else 'done'
                )
            else:
                results['final'] = {
                    'match_rate': diagnosis['current_match_rate'],
                    'status': 'done',
                    'needs_cursor_attention': False
                }
        
        except Exception as e:
            logger.error(f"❌ 智能体循环出错: {e}", exc_info=True)
            results['error'] = str(e)
            
            # 保存错误上下文
            diagnosis = self.server.run_physics_diagnosis()
            self.save_context_for_cursor(
                stage='error',
                diagnosis=diagnosis,
                action_taken='loop_failed',
                next_action='fix_error'
            )
        
        return results


def main():
    parser = argparse.ArgumentParser(description='V10.3 Cursor智能体工作流')
    parser.add_argument('--mode', type=str, default='auto',
                       choices=['auto', 'observation', 'thinking', 'action'],
                       help='运行模式')
    
    args = parser.parse_args()
    
    agent = CursorAgentLoop()
    
    if args.mode == 'auto':
        results = agent.run_full_loop()
        
        # 输出最终结果
        print("\n" + "="*80)
        print("📊 智能体工作流完成")
        print("="*80)
        print(f"最终匹配率: {results.get('final', {}).get('match_rate', 0):.1f}%")
        print(f"状态: {results.get('final', {}).get('status', 'unknown')}")
        
        if results.get('final', {}).get('needs_cursor_attention'):
            print("\n⚠️  需要Cursor关注:")
            print("   - 需要修改代码进行逻辑重构")
            print("   - 请查看 config/cursor_context.json 了解详情")
            print("   - 修改代码后，重新运行此脚本")
        
        print("="*80 + "\n")
    elif args.mode == 'observation':
        agent.run_observation()
    elif args.mode == 'thinking':
        diagnosis = agent.run_observation()
        agent.run_thinking(diagnosis)
    elif args.mode == 'action':
        diagnosis = agent.run_observation()
        decision = agent.run_thinking(diagnosis)
        agent.run_action(decision)


if __name__ == '__main__':
    main()

