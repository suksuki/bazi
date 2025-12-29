#!/usr/bin/env python3
"""
FDS-V1.1 重新拟合脚本：A-03 羊刃架杀（对齐V2.0规范）
执行Step 2-5的完整拟合工作，重点：
- Step 3: 计算质心并归一化
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
    calculate_cosine_similarity
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDSV11RefitEngine:
    """
    FDS-V1.1 重新拟合引擎（V2.0对齐版）
    执行Step 2-5的拟合工作，重点计算质心和更新feature_anchors
    """
    
    def __init__(self, pattern_id: str = 'A-03'):
        self.pattern_id = pattern_id
        self.controller = HolographicPatternController()
        self.framework = QuantumUniversalFramework()
        self.registry_loader = RegistryLoader()
        self.pattern = self.controller.get_pattern_by_id(pattern_id)
        
        if not self.pattern:
            raise ValueError(f"格局 {pattern_id} 不存在")
        
        logger.info(f"初始化FDS-V1.1重新拟合引擎: {pattern_id}")
    
    def load_existing_fitting_data(self) -> Dict[str, Any]:
        """
        加载现有的拟合数据（如果有）
        
        Returns:
            拟合数据字典，包含step3的results
        """
        fitting_file = project_root / "data" / "holographic_pattern" / "A-03_FDS_Fitting_Results.json"
        
        if fitting_file.exists():
            logger.info(f"加载现有拟合数据: {fitting_file}")
            with open(fitting_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("未找到现有拟合数据，需要重新执行Step 2")
            return {}
    
    def step3_calculate_centroids(self, fitting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: 多维特征提取与锚点锁定
        计算Tier A和Tier X的质心
        
        Args:
            fitting_data: 现有拟合数据（包含step3.results）
            
        Returns:
            质心计算结果
        """
        logger.info("=" * 70)
        logger.info("Step 3: 多维特征提取与锚点锁定（计算质心）")
        logger.info("=" * 70)
        
        step3_data = fitting_data.get('step3', {})
        results = step3_data.get('results', [])
        
        if not results:
            raise ValueError("未找到Step 3的拟合结果，请先执行Step 2和Step 3")
        
        logger.info(f"处理 {len(results)} 个样本...")
        
        # 1. 提取Tier A样本的5维投影值（需要归一化）
        tier_a_projections = []
        tier_x_projections = []
        
        for result in results:
            # 优先使用frequency_vector重新计算projection（基于实际能量分布）
            # 如果frequency_vector不存在，则使用原始projection
            frequency_vector = result.get('frequency_vector', {})
            
            if frequency_vector:
                # 基于frequency_vector计算5维投影
                # 映射关系：
                # E (能级轴): 比劫 + 印枭（自我团队+资源支持 = 根基）
                # O (秩序轴): 官杀（权力、地位）
                # M (物质轴): 财星（财富、资产）
                # S (应力轴): 官杀 - 印枭（压力 - 支撑 = 应力）
                # R (关联轴): 食伤（输出、表达 = 人际）
                
                bi_jie = frequency_vector.get('比劫', 0.0)
                shi_shang = frequency_vector.get('食伤', 0.0)
                cai_xing = frequency_vector.get('财星', 0.0)
                guan_sha = frequency_vector.get('官杀', 0.0)
                yin_xiao = frequency_vector.get('印枭', 0.0)
                
                # 计算总能量（用于归一化）
                total_energy = bi_jie + shi_shang + cai_xing + guan_sha + yin_xiao
                
                if total_energy > 0:
                    # 计算5维投影（归一化）
                    projection = {
                        'E': (bi_jie + yin_xiao) / total_energy,  # 能级轴：根基
                        'O': guan_sha / total_energy,              # 秩序轴：权力
                        'M': cai_xing / total_energy,              # 物质轴：财富
                        'S': max(0, (guan_sha - yin_xiao)) / total_energy if total_energy > 0 else 0,  # 应力轴：压力-支撑
                        'R': shi_shang / total_energy              # 关联轴：输出
                    }
                    # 确保归一化
                    normalized_projection = tensor_normalize(projection)
                else:
                    # 如果总能量为0，使用原始projection
                    projection = result.get('projection', {})
                    normalized_projection = tensor_normalize(projection) if projection else None
            else:
                # 使用原始projection
                projection = result.get('projection', {})
                normalized_projection = tensor_normalize(projection) if projection else None
            
            if not normalized_projection:
                continue
            
            # 判断是否为Tier X（根据规范：极值法则、相变法则、算法失效法则）
            sai = result.get('sai', 0.0)
            s_value = normalized_projection.get('S', 0.0)
            e_value = normalized_projection.get('E', 0.0)
            
            # Tier X判断：
            # 1. 极值法则：S轴或E轴异常高（>0.5）
            # 2. 相变法则：S轴极高且E轴极低（结构高压）
            is_tier_x = False
            if s_value > 0.5:  # 应力轴异常高
                is_tier_x = True
            elif e_value > 0.5 and s_value > 0.3:  # 能级溢出且高应力
                is_tier_x = True
            elif sai > 2.0:  # SAI异常高
                is_tier_x = True
            
            if is_tier_x:
                tier_x_projections.append(normalized_projection)
            else:
                tier_a_projections.append(normalized_projection)
        
        logger.info(f"Tier A样本数: {len(tier_a_projections)}")
        logger.info(f"Tier X样本数: {len(tier_x_projections)}")
        
        # 2. 计算Tier A质心
        standard_centroid = None
        if tier_a_projections:
            standard_centroid = calculate_centroid(tier_a_projections)
            logger.info(f"✅ Tier A质心计算完成: {standard_centroid}")
        
        # 3. 计算Tier X质心（如果有多个变体，需要分组）
        singularity_centroids = []
        if tier_x_projections:
            # 简化：将所有Tier X样本作为一个整体计算质心
            # 实际应该根据不同的奇点类型分组（如A-03-X1, A-03-X2）
            x1_projections = []
            x2_projections = []
            
            for proj in tier_x_projections:
                # 根据应力轴S值判断是X1（高能溢出）还是X2（高压屈服）
                if proj.get('S', 0.0) > 0.4:
                    x2_projections.append(proj)  # 高压屈服型
                else:
                    x1_projections.append(proj)  # 聚变临界型
            
            if x1_projections:
                x1_centroid = calculate_centroid(x1_projections)
                singularity_centroids.append({
                    'sub_id': 'A-03-X1',
                    'description': '聚变临界型 (Tier X1 Mean)',
                    'vector': x1_centroid,
                    'match_threshold': 0.90,
                    'risk_level': 'CRITICAL',
                    'special_instruction': 'Enable Vent Logic (Disable Balance Check)',
                    'sample_count': len(x1_projections)
                })
                logger.info(f"✅ Tier X1质心计算完成: {x1_centroid}")
            
            if x2_projections:
                x2_centroid = calculate_centroid(x2_projections)
                singularity_centroids.append({
                    'sub_id': 'A-03-X2',
                    'description': '结构高压屈服型 (Tier X2 Mean)',
                    'vector': x2_centroid,
                    'match_threshold': 0.90,
                    'risk_level': 'CRITICAL',
                    'special_instruction': 'Disable Balance Check',
                    'sample_count': len(x2_projections)
                })
                logger.info(f"✅ Tier X2质心计算完成: {x2_centroid}")
        
        return {
            'standard_centroid': standard_centroid,
            'singularity_centroids': singularity_centroids,
            'tier_a_count': len(tier_a_projections),
            'tier_x_count': len(tier_x_projections)
        }
    
    def step5_update_registry(self, centroids: Dict[str, Any]) -> bool:
        """
        Step 5: 专题封卷与全息注册
        更新feature_anchors到注册表
        
        Args:
            centroids: Step 3计算的质心结果
            
        Returns:
            是否更新成功
        """
        logger.info("=" * 70)
        logger.info("Step 5: 专题封卷与全息注册（更新feature_anchors）")
        logger.info("=" * 70)
        
        registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
        
        # 加载注册表
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        pattern = registry['patterns'].get(self.pattern_id)
        if not pattern:
            logger.error(f"格局 {self.pattern_id} 不存在于注册表")
            return False
        
        # 更新feature_anchors
        standard_centroid = centroids.get('standard_centroid')
        singularity_centroids = centroids.get('singularity_centroids', [])
        
        if not standard_centroid:
            logger.error("缺少standard_centroid，无法更新注册表")
            return False
        
        # 构建feature_anchors结构
        feature_anchors = {
            'description': '基于大数据拟合算出的空间质心坐标 (The DNA of Fate)',
            'standard_centroid': {
                'description': '标准恒星锚点 (Tier A Mean)',
                'vector': standard_centroid,
                'match_threshold': 0.80,
                'perfect_threshold': 0.92
            },
            'singularity_centroids': singularity_centroids
        }
        
        # 更新注册表
        pattern['feature_anchors'] = feature_anchors
        
        # 更新版本历史
        if 'audit_trail' not in pattern:
            pattern['audit_trail'] = {}
        
        if 'version_history' not in pattern['audit_trail']:
            pattern['audit_trail']['version_history'] = []
        
        pattern['audit_trail']['version_history'].append({
            'version': '2.0',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'FDS-V1.1 Refit (V2.0 Alignment)',
            'description': '重新拟合，计算质心锚点并更新feature_anchors',
            'fds_steps': {
                'step3': f'计算质心（Tier A: {centroids.get("tier_a_count", 0)}, Tier X: {centroids.get("tier_x_count", 0)}）',
                'step5': '更新feature_anchors到注册表'
            }
        })
        
        # 保存注册表
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 注册表已更新: {registry_path}")
        logger.info(f"   - standard_centroid: {standard_centroid}")
        logger.info(f"   - singularity_centroids: {len(singularity_centroids)} 个")
        
        return True
    
    def run_full_refit(self) -> Dict[str, Any]:
        """
        执行完整的重新拟合流程
        
        Returns:
            拟合结果字典
        """
        logger.info("=" * 70)
        logger.info("🚀 开始A-03羊刃架杀重新拟合（对齐V2.0规范）")
        logger.info("=" * 70)
        
        # 1. 加载现有拟合数据
        fitting_data = self.load_existing_fitting_data()
        
        if not fitting_data.get('step3', {}).get('results'):
            logger.error("未找到Step 3的拟合结果，请先执行Step 2和Step 3")
            return {'error': '缺少Step 3拟合数据'}
        
        # 2. Step 3: 计算质心
        centroids = self.step3_calculate_centroids(fitting_data)
        
        # 3. Step 5: 更新注册表
        update_success = self.step5_update_registry(centroids)
        
        if not update_success:
            return {'error': '注册表更新失败'}
        
        # 4. 验证更新结果
        updated_pattern = self.registry_loader.get_pattern(self.pattern_id)
        feature_anchors = updated_pattern.get('feature_anchors', {})
        
        result = {
            'pattern_id': self.pattern_id,
            'refit_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fds_version': 'V1.1 (V2.0 Alignment)',
            'step3_centroids': centroids,
            'step5_registry_updated': update_success,
            'verification': {
                'feature_anchors_exists': 'feature_anchors' in updated_pattern,
                'standard_centroid_exists': 'standard_centroid' in feature_anchors,
                'singularity_centroids_count': len(feature_anchors.get('singularity_centroids', []))
            }
        }
        
        logger.info("=" * 70)
        logger.info("✅ 重新拟合完成！")
        logger.info("=" * 70)
        logger.info(f"   - Tier A质心: {centroids.get('standard_centroid')}")
        logger.info(f"   - Tier X质心数: {len(centroids.get('singularity_centroids', []))}")
        logger.info(f"   - 注册表已更新: {update_success}")
        
        return result


if __name__ == '__main__':
    engine = FDSV11RefitEngine('A-03')
    result = engine.run_full_refit()
    
    # 保存结果
    output_file = project_root / "data" / "holographic_pattern" / "A-03_Refit_V2_Results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_file}")

