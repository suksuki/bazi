#!/usr/bin/env python3
"""
FDS-V1.4 重新拟合脚本：A-03 羊刃架杀（对齐V2.1规范）
使用新的transfer_matrix重新计算feature_anchors（质心）

重点：
- Step 3: 使用transfer_matrix计算5维投影，重新计算质心
- Step 5: 更新feature_anchors到注册表
"""

import sys
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.registry_loader import RegistryLoader
from core.math_engine import (
    calculate_centroid,
    tensor_normalize,
    project_tensor_with_matrix
)
from core.physics_engine import compute_energy_flux

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDSV14RefitEngine:
    """
    FDS-V1.4 重新拟合引擎（V2.1对齐版）
    使用transfer_matrix重新计算质心
    """
    
    def __init__(self, pattern_id: str = 'A-03'):
        self.pattern_id = pattern_id
        self.controller = HolographicPatternController()
        self.framework = QuantumUniversalFramework()
        self.registry_loader = RegistryLoader()
        self.pattern = self.controller.get_pattern_by_id(pattern_id)
        
        if not self.pattern:
            raise ValueError(f"格局 {pattern_id} 不存在")
        
        logger.info(f"初始化FDS-V1.4重新拟合引擎: {pattern_id}")
    
    def load_fitting_data(self) -> Dict[str, Any]:
        """加载现有拟合数据（优先使用Step 2全量海选结果）"""
        # 优先使用Step 2全量海选结果
        step2_file = project_root / "data" / "holographic_pattern" / "A-03_Step2_FullScan_Results.json"
        if step2_file.exists():
            logger.info(f"加载Step 2全量海选结果: {step2_file}")
            with open(step2_file, 'r', encoding='utf-8') as f:
                step2_data = json.load(f)
            
            # 转换为Step 3格式
            tier_a_samples = step2_data.get('tier_a_samples', [])
            tier_x_samples = step2_data.get('tier_x_samples', [])
            
            # 构建results格式（用于Step 3）
            results = []
            for sample in tier_a_samples + tier_x_samples:
                results.append({
                    'chart': sample['chart'],
                    'day_master': sample['day_master'],
                    'purity_score': sample.get('purity_score', 0.0),
                    'singularity_protocol': sample.get('singularity_protocol', {})
                })
            
            return {
                'step3': {
                    'results': results
                }
            }
        
        # 回退到旧的拟合数据
        fitting_file = project_root / "data" / "holographic_pattern" / "A-03_FDS_Fitting_Results.json"
        if fitting_file.exists():
            logger.info(f"加载现有拟合数据: {fitting_file}")
            with open(fitting_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("未找到现有拟合数据，需要重新执行Step 2")
            return {}
    
    def calculate_frequency_vector(self, chart: List[str], day_master: str) -> Dict[str, float]:
        """
        计算十神频率向量（用于transfer_matrix输入）
        
        Returns:
            {"parallel": float, "resource": float, "power": float, "wealth": float, "output": float}
        """
        parallel = compute_energy_flux(chart, day_master, "比肩") + \
                   compute_energy_flux(chart, day_master, "劫财")
        resource = compute_energy_flux(chart, day_master, "正印") + \
                   compute_energy_flux(chart, day_master, "偏印")
        power = compute_energy_flux(chart, day_master, "七杀") + \
                compute_energy_flux(chart, day_master, "正官")
        wealth = compute_energy_flux(chart, day_master, "正财") + \
                 compute_energy_flux(chart, day_master, "偏财")
        output = compute_energy_flux(chart, day_master, "食神") + \
                 compute_energy_flux(chart, day_master, "伤官")
        
        return {
            "parallel": parallel,
            "resource": resource,
            "power": power,
            "wealth": wealth,
            "output": output
        }
    
    def step3_calculate_centroids_with_matrix(
        self,
        fitting_data: Dict[str, Any],
        transfer_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Step 3: 使用transfer_matrix计算质心（V2.1）
        
        Args:
            fitting_data: 现有拟合数据（包含step3.results）
            transfer_matrix: 5x5转换矩阵
            
        Returns:
            质心计算结果
        """
        logger.info("=" * 70)
        logger.info("Step 3: 使用transfer_matrix计算质心（V2.1）")
        logger.info("=" * 70)
        
        step3_data = fitting_data.get('step3', {})
        results = step3_data.get('results', [])
        
        if not results:
            raise ValueError("未找到Step 3的拟合结果，请先执行Step 2和Step 3")
        
        logger.info(f"处理 {len(results)} 个样本...")
        
        # 1. 提取Tier A和Tier X样本
        tier_a_projections = []
        tier_x_projections = []
        
        for result in results:
            chart = result.get('chart', [])
            day_master = result.get('day_master', '')
            
            if not chart or not day_master:
                continue
            
            # 计算十神频率向量
            frequency_vector = self.calculate_frequency_vector(chart, day_master)
            
            # 使用transfer_matrix计算5维投影
            projection = project_tensor_with_matrix(frequency_vector, transfer_matrix)
            
            # 归一化投影
            normalized_projection = tensor_normalize(projection)
            
            # 判断是否为Tier X（根据singularity_protocol）
            singularity_protocol = result.get('singularity_protocol', {})
            is_singularity = (
                singularity_protocol.get('law_of_extremum', False) or
                singularity_protocol.get('law_of_phase_change', False) or
                singularity_protocol.get('law_of_algorithm_failure', False)
            )
            
            if is_singularity:
                tier_x_projections.append(normalized_projection)
            else:
                tier_a_projections.append(normalized_projection)
        
        logger.info(f"Tier A样本数: {len(tier_a_projections)}")
        logger.info(f"Tier X样本数: {len(tier_x_projections)}")
        
        # 2. 计算质心
        standard_centroid = None
        singularity_centroids = []
        
        if tier_a_projections:
            standard_centroid = calculate_centroid(tier_a_projections)
            logger.info(f"Tier A质心: {standard_centroid}")
        
        if tier_x_projections:
            # 按sub_id分组（如果有）
            tier_x_groups = {}
            tier_x_idx = 0  # Tier X投影的索引
            
            for result in results:
                singularity_protocol = result.get('singularity_protocol', {})
                if (singularity_protocol.get('law_of_extremum', False) or
                    singularity_protocol.get('law_of_phase_change', False) or
                    singularity_protocol.get('law_of_algorithm_failure', False)):
                    sub_id = singularity_protocol.get('sub_id', 'X1')
                    if sub_id not in tier_x_groups:
                        tier_x_groups[sub_id] = []
                    
                    # 使用tier_x_idx而不是results的索引
                    if tier_x_idx < len(tier_x_projections):
                        tier_x_groups[sub_id].append(tier_x_projections[tier_x_idx])
                        tier_x_idx += 1
            
            # 计算每个组的质心
            for sub_id, projections in tier_x_groups.items():
                centroid = calculate_centroid(projections)
                singularity_centroids.append({
                    'sub_id': sub_id,
                    'vector': centroid,
                    'sample_count': len(projections)
                })
                logger.info(f"{sub_id}质心: {centroid} (样本数: {len(projections)})")
        
        return {
            'standard_centroid': standard_centroid,
            'singularity_centroids': singularity_centroids,
            'tier_a_count': len(tier_a_projections),
            'tier_x_count': len(tier_x_projections)
        }
    
    def step5_update_registry(
        self,
        centroids: Dict[str, Any]
    ) -> bool:
        """
        Step 5: 更新feature_anchors到注册表
        
        Args:
            centroids: 质心计算结果
            
        Returns:
            是否成功
        """
        logger.info("=" * 70)
        logger.info("Step 5: 更新feature_anchors到注册表（V2.1）")
        logger.info("=" * 70)
        
        registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
        
        # 读取注册表
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        pattern = registry.get('patterns', {}).get(self.pattern_id)
        if not pattern:
            logger.error(f"格局 {self.pattern_id} 不存在于注册表")
            return False
        
        # 更新feature_anchors
        if 'feature_anchors' not in pattern:
            pattern['feature_anchors'] = {}
        
        # 更新standard_centroid
        standard_centroid = centroids.get('standard_centroid')
        if standard_centroid:
            if 'standard_centroid' not in pattern['feature_anchors']:
                pattern['feature_anchors']['standard_centroid'] = {}
            
            pattern['feature_anchors']['standard_centroid']['vector'] = standard_centroid
            pattern['feature_anchors']['standard_centroid']['description'] = "标准恒星锚点 (Tier A Mean) - 基于transfer_matrix计算"
            logger.info(f"✅ 已更新standard_centroid: {standard_centroid}")
        
        # 更新singularity_centroids
        singularity_centroids = centroids.get('singularity_centroids', [])
        if singularity_centroids:
            if 'singularity_centroids' not in pattern['feature_anchors']:
                pattern['feature_anchors']['singularity_centroids'] = []
            
            # 更新现有的或添加新的
            existing_subs = {s.get('sub_id'): s for s in pattern['feature_anchors'].get('singularity_centroids', [])}
            
            for new_centroid in singularity_centroids:
                sub_id = new_centroid['sub_id']
                if sub_id in existing_subs:
                    # 更新现有
                    existing_subs[sub_id]['vector'] = new_centroid['vector']
                    existing_subs[sub_id]['sample_count'] = new_centroid['sample_count']
                    existing_subs[sub_id]['description'] = f"{sub_id}质心 - 基于transfer_matrix计算"
                else:
                    # 添加新的
                    existing_subs[sub_id] = {
                        'sub_id': sub_id,
                        'vector': new_centroid['vector'],
                        'sample_count': new_centroid['sample_count'],
                        'description': f"{sub_id}质心 - 基于transfer_matrix计算",
                        'match_threshold': 0.9,
                        'risk_level': 'CRITICAL'
                    }
            
            pattern['feature_anchors']['singularity_centroids'] = list(existing_subs.values())
            logger.info(f"✅ 已更新singularity_centroids: {len(singularity_centroids)}个")
        
        # 更新版本信息
        pattern['version'] = '2.1'
        pattern['updated_at'] = datetime.now().strftime('%Y-%m-%d')
        
        # 保存注册表
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 注册表已更新: {registry_path}")
        return True
    
    def run_refit(self) -> Dict[str, Any]:
        """执行完整的重新拟合流程"""
        logger.info("=" * 70)
        logger.info("🚀 开始FDS-V1.4重新拟合：A-03 羊刃架杀（V2.1）")
        logger.info("=" * 70)
        
        # 1. 加载现有拟合数据
        fitting_data = self.load_fitting_data()
        
        # 2. 获取transfer_matrix
        physics_kernel = self.pattern.get('physics_kernel', {})
        transfer_matrix = physics_kernel.get('transfer_matrix')
        
        if not transfer_matrix:
            raise ValueError("格局缺少transfer_matrix配置，请先升级到V2.1")
        
        logger.info("✅ 已加载transfer_matrix")
        
        # 3. Step 3: 使用transfer_matrix计算质心
        centroids = self.step3_calculate_centroids_with_matrix(fitting_data, transfer_matrix)
        
        # 4. Step 5: 更新注册表
        success = self.step5_update_registry(centroids)
        
        if not success:
            raise RuntimeError("更新注册表失败")
        
        # 5. 保存结果
        result = {
            'pattern_id': self.pattern_id,
            'refit_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fds_version': 'V1.4',
            'registry_version': '2.1',
            'step3': centroids
        }
        
        output_file = project_root / "data" / "holographic_pattern" / "A-03_Refit_V21_Results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 结果已保存: {output_file}")
        
        return result


if __name__ == '__main__':
    try:
        engine = FDSV14RefitEngine('A-03')
        result = engine.run_refit()
        
        print("\n" + "=" * 70)
        print("✅ FDS-V1.4重新拟合完成！")
        print("=" * 70)
        print(f"Tier A质心: {result['step3']['standard_centroid']}")
        print(f"Tier X质心数: {len(result['step3']['singularity_centroids'])}")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"重新拟合失败: {e}", exc_info=True)
        sys.exit(1)

