"""
V11.1 数据加载器 (Data Loader)
融合模组：加权混合不同类型的数据

训练集配比：
- 核心层 (Core): 经典古籍案例，权重 3.0 —— 不可动摇的宪法
- 骨架层 (Skeleton): 合成理论数据，权重 2.0 —— 撑起模型的骨架
- 肌肉层 (Muscle): 清洗后的现代数据，权重 1.0 —— 增加泛化能力

验证集 (Validation Set):
- 严禁包含合成数据，必须是 100% 真实案例（"练假打真"）
"""

import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models.config_model import ConfigModel
from .synthetic_factory import SyntheticDataFactory
from .dynamic_cleaner import DynamicCleaner

logger = logging.getLogger(__name__)

# 数据权重配置（可通过配置文件覆盖）
DEFAULT_WEIGHTS = {
    'classic': 3.0,      # 核心层：经典案例权重最高
    'synthetic': 2.0,    # 骨架层：合成数据权重中等
    'modern': 1.0        # 肌肉层：现代数据权重最低
}


class DataLoader:
    """数据加载器：加权混合不同类型的数据"""
    
    def __init__(self, config_model: ConfigModel = None):
        self.config_model = config_model or ConfigModel()
        self.data_dir = project_root / "data"
        self.synthetic_factory = SyntheticDataFactory()
        self.dynamic_cleaner = DynamicCleaner(config_model=config_model)
    
    def load_training_data(
        self,
        use_dynamic_cleaning: bool = True,
        generate_synthetic: bool = True,
        synthetic_count: int = 50
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[bool], List[Dict]]:
        """
        加载训练数据（包含样本权重）
        
        Args:
            use_dynamic_cleaning: 是否使用动态清洗
            generate_synthetic: 是否生成合成数据
            synthetic_count: 合成数据生成数量
        
        Returns:
            Tuple[X, y, sample_weights, is_synthetic, metadata_list]:
            - X: 特征矩阵
            - y: 标签向量
            - sample_weights: 样本权重数组
            - is_synthetic: 是否合成的标记列表
            - metadata_list: 案例元数据列表（用于调试和分析）
        """
        logger.info("📦 开始加载训练数据...")
        
        # 1. 加载经典案例（Core Layer）
        classic_cases = self._load_classic_cases()
        logger.info(f"   ✅ 加载了 {len(classic_cases)} 个经典案例（权重 {WEIGHTS['classic']:.1f}）")
        
        # 2. 生成合成数据（Skeleton Layer）
        synthetic_cases = []
        if generate_synthetic:
            synthetic_cases = self.synthetic_factory.generate_perfect_cases(target_count=synthetic_count)
            logger.info(f"   ✅ 生成了 {len(synthetic_cases)} 个合成案例（权重 {WEIGHTS['synthetic']:.1f}）")
        
        # 3. 加载现代案例（Muscle Layer）
        modern_cases = self._load_modern_cases()
        logger.info(f"   ✅ 加载了 {len(modern_cases)} 个现代案例（原始）")
        
        # 4. 动态清洗现代案例（如果启用）
        cleaned_modern_cases = modern_cases
        if use_dynamic_cleaning and len(classic_cases) > 0:
            cleaned_modern_cases, dirty_ids = self.dynamic_cleaner.filter_outliers(
                classic_cases=classic_cases,
                synthetic_cases=synthetic_cases,
                modern_cases=modern_cases,
                confidence_threshold=0.90,
                use_svm=True
            )
            logger.info(f"   ✅ 动态清洗后剩余 {len(cleaned_modern_cases)} 个现代案例（权重 {WEIGHTS['modern']:.1f}）")
            if dirty_ids:
                logger.info(f"   🚫 识别并排除了 {len(dirty_ids)} 个脏数据")
        
        # 5. 合并所有数据
        all_cases = classic_cases + synthetic_cases + cleaned_modern_cases
        
        # 6. 标记数据来源
        is_synthetic_list = []
        sample_weights = []
        metadata_list = []
        
        for case in all_cases:
            # 判断数据来源
            is_synthetic = case.get('synthetic', False)
            category = case.get('category', 'unknown')
            
            # 确定权重
            if category == 'classic' or case.get('id', '').startswith('CLASSIC_'):
                weight = WEIGHTS['classic']
                source = 'classic'
            elif is_synthetic or category == 'synthetic':
                weight = WEIGHTS['synthetic']
                source = 'synthetic'
            else:
                weight = WEIGHTS['modern']
                source = 'modern'
            
            is_synthetic_list.append(is_synthetic)
            sample_weights.append(weight)
            metadata_list.append({
                'id': case.get('id', ''),
                'name': case.get('name', ''),
                'source': source,
                'weight': weight,
                'synthetic': is_synthetic
            })
        
        logger.info(f"   📊 数据统计:")
        logger.info(f"      经典案例: {sum(1 for m in metadata_list if m['source'] == 'classic')} 个（权重 {WEIGHTS['classic']:.1f}）")
        logger.info(f"      合成案例: {sum(1 for m in metadata_list if m['source'] == 'synthetic')} 个（权重 {WEIGHTS['synthetic']:.1f}）")
        logger.info(f"      现代案例: {sum(1 for m in metadata_list if m['source'] == 'modern')} 个（权重 {WEIGHTS['modern']:.1f}）")
        
        # 7. 提取特征和标签（需要传入engine）
        # 这里只返回数据和元数据，特征提取在trainer中完成
        # 返回占位符，实际特征提取在调用方完成
        X_placeholder = np.array([])  # 占位符，实际应在trainer中提取
        y_placeholder = np.array([])  # 占位符，实际应在trainer中提取
        
        return X_placeholder, y_placeholder, np.array(sample_weights), is_synthetic_list, metadata_list
    
    def load_training_cases(
        self,
        use_dynamic_cleaning: bool = True,
        generate_synthetic: bool = True,
        synthetic_count: int = 50,
        classic_weight: float = None,
        synthetic_weight: float = None,
        modern_weight: float = None
    ) -> Tuple[List[Dict], List[float], List[bool]]:
        """
        加载训练案例列表（用于特征提取）
        
        Returns:
            Tuple[cases, sample_weights, is_synthetic]:
            - cases: 案例列表
            - sample_weights: 样本权重列表
            - is_synthetic: 是否合成的标记列表
        """
        logger.info("📦 开始加载训练案例...")
        
        # 1. 加载经典案例
        classic_cases = self._load_classic_cases()
        logger.info(f"   ✅ 加载了 {len(classic_cases)} 个经典案例")
        
        # 2. 生成合成数据
        synthetic_cases = []
        if generate_synthetic:
            synthetic_cases = self.synthetic_factory.generate_perfect_cases(target_count=synthetic_count)
            logger.info(f"   ✅ 生成了 {len(synthetic_cases)} 个合成案例")
        
        # 3. 加载并清洗现代案例
        modern_cases = self._load_modern_cases()
        cleaned_modern_cases = modern_cases
        if use_dynamic_cleaning and len(classic_cases) > 0:
            cleaned_modern_cases, dirty_ids = self.dynamic_cleaner.filter_outliers(
                classic_cases=classic_cases,
                synthetic_cases=synthetic_cases,
                modern_cases=modern_cases,
                confidence_threshold=0.90,
                use_svm=True
            )
            if dirty_ids:
                logger.info(f"   🚫 识别并排除了 {len(dirty_ids)} 个脏数据")
        
        # 4. 合并并标记
        all_cases = classic_cases + synthetic_cases + cleaned_modern_cases
        
        # 使用传入的权重或默认权重
        weights = {
            'classic': classic_weight if classic_weight is not None else DEFAULT_WEIGHTS['classic'],
            'synthetic': synthetic_weight if synthetic_weight is not None else DEFAULT_WEIGHTS['synthetic'],
            'modern': modern_weight if modern_weight is not None else DEFAULT_WEIGHTS['modern']
        }
        
        sample_weights = []
        is_synthetic_list = []
        
        for case in all_cases:
            is_synthetic = case.get('synthetic', False)
            category = case.get('category', 'unknown')
            
            if category == 'classic' or case.get('id', '').startswith('CLASSIC_'):
                weight = weights['classic']
            elif is_synthetic or category == 'synthetic':
                weight = weights['synthetic']
            else:
                weight = weights['modern']
            
            sample_weights.append(weight)
            is_synthetic_list.append(is_synthetic)
        
        logger.info(f"   📊 总计: {len(all_cases)} 个案例")
        # 统计各类别数量
        classic_weight = weights['classic']
        classic_count = sum(1 for i, s in enumerate(is_synthetic_list) if not s and sample_weights[i] == classic_weight)
        synthetic_count = sum(is_synthetic_list)
        modern_count = len(all_cases) - classic_count - synthetic_count
        logger.info(f"      经典: {classic_count} 个")
        logger.info(f"      合成: {synthetic_count} 个")
        logger.info(f"      现代: {modern_count} 个")
        
        return all_cases, sample_weights, is_synthetic_list
    
    def _load_classic_cases(self) -> List[Dict]:
        """加载经典案例"""
        classic_file = self.data_dir / "classic_cases.json"
        classic_cases = []
        
        if classic_file.exists():
            with open(classic_file, 'r', encoding='utf-8') as f:
                classic_cases = json.load(f)
                # 确保标记为classic
                for case in classic_cases:
                    case['category'] = 'classic'
                    case['synthetic'] = False
        
        return classic_cases
    
    def _load_modern_cases(self) -> List[Dict]:
        """加载现代案例（排除已忽略的）"""
        ignored_ids = self.dynamic_cleaner.load_ignored_cases()
        
        calibration_file = self.data_dir / "calibration_cases.json"
        modern_cases = []
        
        if calibration_file.exists():
            with open(calibration_file, 'r', encoding='utf-8') as f:
                cal_cases = json.load(f)
                
                # 过滤：排除classic、synthetic和已忽略的
                classic_ids = set()
                classic_file = self.data_dir / "classic_cases.json"
                if classic_file.exists():
                    with open(classic_file, 'r', encoding='utf-8') as f:
                        classic_cases = json.load(f)
                        classic_ids = {c.get('id') for c in classic_cases}
                
                for case in cal_cases:
                    case_id = case.get('id', '')
                    # 排除：已忽略的、classic的、synthetic的
                    if (case_id not in ignored_ids and 
                        case_id not in classic_ids and 
                        not case.get('synthetic', False)):
                        case['category'] = 'modern'
                        modern_cases.append(case)
        
        return modern_cases


if __name__ == '__main__':
    """测试数据加载器"""
    logging.basicConfig(level=logging.INFO)
    
    loader = DataLoader()
    
    cases, weights, is_synthetic = loader.load_training_cases(
        use_dynamic_cleaning=True,
        generate_synthetic=True,
        synthetic_count=30
    )
    
    print(f"\n✅ 数据加载完成")
    print(f"   总案例数: {len(cases)}")
    print(f"   权重分布: {dict(Counter([f'{w:.1f}' for w in weights]))}")
    print(f"   合成数据: {sum(is_synthetic)} 个")
    print(f"   真实数据: {len(cases) - sum(is_synthetic)} 个")

