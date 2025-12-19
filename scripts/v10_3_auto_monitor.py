#!/usr/bin/env python3
"""
V10.3 自动监控与优化服务
========================

实现自动化的"观察-思考-行动"循环：
1. 定期运行诊断（观察）
2. 如果匹配率低于阈值，自动触发优化（行动）
3. 持续监控，直到达到目标匹配率

使用方法：
    # 后台运行
    nohup python3 scripts/v10_3_auto_monitor.py --daemon &
    
    # 前台运行（带日志）
    python3 scripts/v10_3_auto_monitor.py --interval 3600
"""

import argparse
import time
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_monitor.log'),
        logging.StreamHandler()
    ]
)


class AutoMonitor:
    """
    自动监控与优化服务
    
    实现自动化的"观察-思考-行动"循环
    """
    
    def __init__(self, 
                 target_match_rate: float = 65.0,
                 trigger_threshold: float = 55.0,
                 min_improvement: float = 1.0):
        """
        初始化自动监控器
        
        Args:
            target_match_rate: 目标匹配率（达到后停止优化）
            trigger_threshold: 触发优化的阈值（低于此值自动优化）
            min_improvement: 最小改进幅度（低于此值不触发优化）
        """
        self.server = MCPTuningServer()
        self.driver = AutoDriver()
        self.target_match_rate = target_match_rate
        self.trigger_threshold = trigger_threshold
        self.min_improvement = min_improvement
        self.last_match_rate = None
        self.optimization_count = 0
        
    def run_diagnosis(self) -> Dict[str, Any]:
        """
        运行诊断（观察）
        
        Returns:
            诊断报告
        """
        logger.info("🔍 [观察] 运行物理诊断...")
        diagnosis = self.server.run_physics_diagnosis()
        match_rate = diagnosis['current_match_rate']
        logger.info(f"📊 当前匹配率: {match_rate:.1f}%")
        return diagnosis
    
    def should_optimize(self, diagnosis: Dict[str, Any]) -> bool:
        """
        判断是否需要优化（思考）
        
        Args:
            diagnosis: 诊断报告
            
        Returns:
            是否需要优化
        """
        match_rate = diagnosis['current_match_rate']
        
        # 如果已达到目标，不需要优化
        if match_rate >= self.target_match_rate:
            logger.info(f"✅ 已达到目标匹配率 {self.target_match_rate}%，无需优化")
            return False
        
        # 如果低于触发阈值，需要优化
        if match_rate < self.trigger_threshold:
            logger.info(f"⚠️  匹配率 {match_rate:.1f}% 低于触发阈值 {self.trigger_threshold}%，需要优化")
            return True
        
        # 如果有改进空间，且上次优化有显著提升，继续优化
        if self.last_match_rate is not None:
            improvement = match_rate - self.last_match_rate
            if improvement >= self.min_improvement:
                logger.info(f"📈 上次优化提升了 {improvement:.1f}%，继续优化")
                return True
            else:
                logger.info(f"📉 上次优化提升不足 {self.min_improvement}%，暂停优化")
                return False
        
        # 首次运行，如果低于目标，需要优化
        if match_rate < self.target_match_rate:
            logger.info(f"🎯 首次运行，匹配率 {match_rate:.1f}% 低于目标 {self.target_match_rate}%，开始优化")
            return True
        
        return False
    
    def run_optimization(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行优化（行动）
        
        Args:
            diagnosis: 诊断报告
            
        Returns:
            优化结果
        """
        logger.info("🚀 [行动] 开始自动优化...")
        self.optimization_count += 1
        
        # 根据诊断结果选择优化策略
        main_issues = diagnosis.get('main_issues', [])
        
        # 分析主要问题，决定优化策略
        if any('Special_Strong' in issue['pattern'] for issue in main_issues):
            logger.info("📌 检测到Special_Strong问题，执行逻辑重构（V10.3）")
            # 这里可以调用逻辑重构，但V10.3已经实施，所以继续参数优化
            focus_layer = "threshold"
        elif any('Weak → Strong' in issue['pattern'] or 'Strong → Weak' in issue['pattern'] for issue in main_issues):
            logger.info("📌 检测到Strong↔Weak互判问题，优化结构层")
            focus_layer = "structure"
        else:
            logger.info("📌 执行全量优化")
            focus_layer = "all"
        
        # 执行优化
        try:
            result = self.driver.run_full_auto(
                phase1_trials=50,
                phase2_trials=50,
                phase3_trials=50
            )
            
            # 更新最后匹配率
            final_diagnosis = self.server.run_physics_diagnosis()
            self.last_match_rate = final_diagnosis['current_match_rate']
            
            logger.info(f"✅ 优化完成，新匹配率: {self.last_match_rate:.1f}%")
            return result
        except Exception as e:
            logger.error(f"❌ 优化失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def run_loop(self, interval: int = 3600, max_iterations: Optional[int] = None):
        """
        运行监控循环
        
        Args:
            interval: 检查间隔（秒）
            max_iterations: 最大迭代次数（None表示无限）
        """
        logger.info("="*80)
        logger.info("🤖 自动监控服务启动")
        logger.info("="*80)
        logger.info(f"目标匹配率: {self.target_match_rate}%")
        logger.info(f"触发阈值: {self.trigger_threshold}%")
        logger.info(f"检查间隔: {interval}秒 ({interval/60:.1f}分钟)")
        logger.info("="*80)
        
        iteration = 0
        while True:
            iteration += 1
            if max_iterations and iteration > max_iterations:
                logger.info(f"达到最大迭代次数 {max_iterations}，停止监控")
                break
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 第 {iteration} 次检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*80}")
            
            try:
                # 1. 观察：运行诊断
                diagnosis = self.run_diagnosis()
                match_rate = diagnosis['current_match_rate']
                
                # 2. 思考：判断是否需要优化
                if not self.should_optimize(diagnosis):
                    logger.info(f"💤 无需优化，等待 {interval} 秒后再次检查...")
                    time.sleep(interval)
                    continue
                
                # 3. 行动：执行优化
                result = self.run_optimization(diagnosis)
                
                # 检查是否达到目标
                if match_rate >= self.target_match_rate:
                    logger.info(f"🎉 已达到目标匹配率 {self.target_match_rate}%，停止优化")
                    break
                
                # 等待后继续
                logger.info(f"⏳ 等待 {interval} 秒后再次检查...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止监控")
                break
            except Exception as e:
                logger.error(f"❌ 监控循环出错: {e}", exc_info=True)
                logger.info(f"⏳ 等待 {interval} 秒后重试...")
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='V10.3 自动监控与优化服务')
    parser.add_argument('--target', type=float, default=65.0,
                       help='目标匹配率（默认: 65.0）')
    parser.add_argument('--trigger', type=float, default=55.0,
                       help='触发优化的阈值（默认: 55.0）')
    parser.add_argument('--interval', type=int, default=3600,
                       help='检查间隔（秒，默认: 3600）')
    parser.add_argument('--max-iterations', type=int, default=None,
                       help='最大迭代次数（默认: 无限）')
    parser.add_argument('--daemon', action='store_true',
                       help='后台运行模式')
    
    args = parser.parse_args()
    
    # 创建日志目录
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    monitor = AutoMonitor(
        target_match_rate=args.target,
        trigger_threshold=args.trigger,
        min_improvement=1.0
    )
    
    if args.daemon:
        # 后台运行（使用nohup或systemd，而不是Python daemon模块）
        logger.warning("⚠️  --daemon选项需要配合nohup使用")
        logger.info("建议使用: nohup python3 scripts/v10_3_auto_monitor.py --interval 3600 &")
        logger.info("或者在前台运行，使用Ctrl+Z和bg命令放到后台")
        # 继续前台运行，但提示用户使用nohup
        monitor.run_loop(interval=args.interval, max_iterations=args.max_iterations)
    else:
        # 前台运行
        monitor.run_loop(interval=args.interval, max_iterations=args.max_iterations)


if __name__ == '__main__':
    main()

