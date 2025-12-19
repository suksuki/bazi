"""
V11.1 动态清洗器 (Dynamic Cleaner)
代谢模组：使用RANSAC思想动态清洗脏数据

机制：
1. 每次训练前，先用Classic和Synthetic数据训练一个基准模型
2. 用基准模型去预测所有Modern数据
3. 偏差检测：如果某Modern案例的预测结果与Ground Truth偏离度 > 阈值，标记为Dirty
4. 处置：自动将其ID追加到config/ignored_cases.json（或在内存中剔除）
"""

import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.models.config_model import ConfigModel

logger = logging.getLogger(__name__)

# 尝试导入sklearn
try:
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️  sklearn未安装，动态清洗器将使用规则方法")


class DynamicCleaner:
    """动态清洗器：自动识别并标记脏数据"""
    
    def __init__(self, config_model: ConfigModel = None):
        self.config_model = config_model or ConfigModel()
        self.config = self.config_model.load_config()
        self.ignored_cases_file = project_root / "config" / "ignored_cases.json"
    
    def load_ignored_cases(self) -> Set[str]:
        """加载已忽略的案例ID"""
        if self.ignored_cases_file.exists():
            with open(self.ignored_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ignored_ids = set(data.get('ignored_case_ids', []))
                logger.info(f"✅ 加载了 {len(ignored_ids)} 个已忽略案例ID")
                return ignored_ids
        return set()
    
    def save_ignored_cases(self, ignored_ids: Set[str], notes: Dict[str, str] = None):
        """保存忽略案例列表"""
        self.ignored_cases_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "V11.1",
            "description": "动态清洗器识别的离群点（脏数据），在训练和评估时排除",
            "ignored_case_ids": sorted(list(ignored_ids)),
            "notes": notes or {},
            "generated_from": "Dynamic Cleaner (V11.1)",
            "total_outliers": len(ignored_ids)
        }
        
        with open(self.ignored_cases_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 已保存 {len(ignored_ids)} 个忽略案例到: {self.ignored_cases_file}")
    
    def filter_outliers(
        self, 
        classic_cases: List[Dict], 
        synthetic_cases: List[Dict],
        modern_cases: List[Dict],
        confidence_threshold: float = 0.90,
        use_svm: bool = True
    ) -> Tuple[List[Dict], Set[str]]:
        """
        使用基准模型过滤离群点
        
        Args:
            classic_cases: 经典案例（基准训练数据）
            synthetic_cases: 合成案例（基准训练数据）
            modern_cases: 现代案例（待清洗数据）
            confidence_threshold: 置信度阈值（预测与ground_truth相反且置信度>阈值时标记为Dirty）
            use_svm: 是否使用SVM作为基准模型（否则使用规则方法）
        
        Returns:
            Tuple[cleaned_modern_cases, new_dirty_ids]: 清洗后的现代案例列表和新增的脏数据ID集合
        """
        logger.info("🧹 开始动态清洗...")
        logger.info(f"   基准数据: {len(classic_cases)} 个经典案例 + {len(synthetic_cases)} 个合成案例")
        logger.info(f"   待清洗数据: {len(modern_cases)} 个现代案例")
        
        # 加载已有的忽略列表
        existing_ignored = self.load_ignored_cases()
        
        # 基准训练数据（Classic + Synthetic）
        reference_cases = classic_cases + synthetic_cases
        
        if len(reference_cases) < 5:
            logger.warning("⚠️  基准数据太少，跳过动态清洗")
            return modern_cases, set()
        
        # 训练基准模型
        if use_svm and SKLEARN_AVAILABLE:
            reference_model, scaler = self._train_reference_svm(reference_cases)
        else:
            reference_model = None
            scaler = None
            logger.info("   使用规则方法作为基准模型")
        
        # 评估现代案例
        dirty_ids = set()
        cleaned_modern_cases = []
        
        engine = GraphNetworkEngine(config=self.config)
        
        for case in modern_cases:
            case_id = case.get('id', '')
            
            # 跳过已经忽略的案例
            if case_id in existing_ignored:
                continue
            
            # 提取特征
            try:
                bazi_list = case.get('bazi', [])
                if isinstance(bazi_list, str):
                    bazi_list = bazi_list.split()
                
                day_master = case.get('day_master', '')
                
                engine.initialize_nodes(
                    bazi=bazi_list,
                    day_master=day_master,
                    luck_pillar=None,
                    year_pillar=None
                )
                
                if use_svm and reference_model is not None:
                    # 使用SVM预测
                    feature_vector = engine.extract_svm_features(day_master)
                    X = np.array([feature_vector])
                    X_scaled = scaler.transform(X)
                    
                    predicted_label = reference_model.predict(X_scaled)[0]
                    prediction_proba = reference_model.predict_proba(X_scaled)[0]
                    confidence = max(prediction_proba)
                    
                    ground_truth = case.get('ground_truth', {}).get('strength', 'Unknown')
                    
                    # 偏差检测：预测与ground_truth相反且置信度很高
                    if predicted_label != ground_truth and confidence > confidence_threshold:
                        dirty_ids.add(case_id)
                        logger.warning(f"   🚫 识别为脏数据: {case_id} ({case.get('name', 'Unknown')})")
                        logger.warning(f"      Ground Truth: {ground_truth}, 预测: {predicted_label}, 置信度: {confidence:.2%}")
                    else:
                        cleaned_modern_cases.append(case)
                
                else:
                    # 使用规则方法（基于calculate_strength_score）
                    result = engine.calculate_strength_score(day_master)
                    predicted_label = result.get('strength_label', 'Unknown')
                    strength_score = result.get('strength_score', 0.0)
                    
                    ground_truth = case.get('ground_truth', {}).get('strength', 'Unknown')
                    
                    # 规则偏差检测：预测与ground_truth完全相反，且分数极端
                    # 例如：ground_truth=Strong但预测=Weak且score<20，或ground_truth=Weak但预测=Strong且score>80
                    is_extreme_mismatch = False
                    if ground_truth == 'Strong' and predicted_label in ['Weak', 'Extreme_Weak'] and strength_score < 20.0:
                        is_extreme_mismatch = True
                    elif ground_truth == 'Weak' and predicted_label == 'Special_Strong' and strength_score > 80.0:
                        is_extreme_mismatch = True
                    elif ground_truth == 'Follower' and predicted_label == 'Special_Strong' and strength_score > 70.0:
                        is_extreme_mismatch = True
                    elif ground_truth == 'Special_Strong' and predicted_label in ['Weak', 'Follower'] and strength_score < 30.0:
                        is_extreme_mismatch = True
                    
                    if is_extreme_mismatch:
                        dirty_ids.add(case_id)
                        logger.warning(f"   🚫 识别为脏数据: {case_id} ({case.get('name', 'Unknown')})")
                        logger.warning(f"      Ground Truth: {ground_truth}, 预测: {predicted_label}, Score: {strength_score:.1f}")
                    else:
                        cleaned_modern_cases.append(case)
            
            except Exception as e:
                logger.error(f"   ❌ 处理案例 {case_id} 时出错: {e}")
                # 出错时保守处理，不标记为脏数据
                cleaned_modern_cases.append(case)
        
        logger.info(f"✅ 动态清洗完成")
        logger.info(f"   清洗后现代案例: {len(cleaned_modern_cases)} 个")
        logger.info(f"   识别出新的脏数据: {len(dirty_ids)} 个")
        
        # 合并到已有的忽略列表
        all_ignored = existing_ignored | dirty_ids
        
        # 保存更新后的忽略列表
        if dirty_ids:
            notes = {}
            for case_id in dirty_ids:
                case = next((c for c in modern_cases if c.get('id') == case_id), None)
                if case:
                    notes[case_id] = f"{case.get('name', case_id)}: 动态清洗器识别为离群点"
            self.save_ignored_cases(all_ignored, notes)
        
        return cleaned_modern_cases, dirty_ids
    
    def _train_reference_svm(self, reference_cases: List[Dict]) -> Tuple[SVC, StandardScaler]:
        """训练基准SVM模型"""
        logger.info("   🔨 训练基准SVM模型...")
        
        engine = GraphNetworkEngine(config=self.config)
        features = []
        labels = []
        
        for case in reference_cases:
            bazi_list = case.get('bazi', [])
            if isinstance(bazi_list, str):
                bazi_list = bazi_list.split()
            
            day_master = case.get('day_master', '')
            
            engine.initialize_nodes(
                bazi=bazi_list,
                day_master=day_master,
                luck_pillar=None,
                year_pillar=None
            )
            
            feature_vector = engine.extract_svm_features(day_master)
            features.append(feature_vector)
            
            ground_truth = case.get('ground_truth', {}).get('strength', 'Unknown')
            labels.append(ground_truth)
        
        X = np.array(features)
        y = np.array(labels)
        
        # 特征标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 训练SVM（使用简单参数）
        svm_model = SVC(kernel='rbf', probability=True, random_state=42)
        svm_model.fit(X_scaled, y)
        
        logger.info(f"   ✅ 基准SVM模型训练完成（{len(reference_cases)} 个样本）")
        
        return svm_model, scaler


if __name__ == '__main__':
    """测试动态清洗器"""
    logging.basicConfig(level=logging.INFO)
    
    # 加载数据
    data_dir = project_root / "data"
    classic_file = data_dir / "classic_cases.json"
    calibration_file = data_dir / "calibration_cases.json"
    
    classic_cases = []
    modern_cases = []
    
    if classic_file.exists():
        with open(classic_file, 'r', encoding='utf-8') as f:
            classic_cases = json.load(f)
    
    if calibration_file.exists():
        with open(calibration_file, 'r', encoding='utf-8') as f:
            cal_cases = json.load(f)
            # 假设calibration_cases中非classic的为modern
            classic_ids = {c.get('id') for c in classic_cases}
            modern_cases = [c for c in cal_cases if c.get('id') not in classic_ids and not c.get('synthetic', False)]
    
    # 创建动态清洗器
    cleaner = DynamicCleaner()
    
    # 生成合成数据（用于基准训练）
    from .synthetic_factory import SyntheticDataFactory
    factory = SyntheticDataFactory()
    synthetic_cases = factory.generate_perfect_cases(target_count=30)
    
    # 执行动态清洗
    cleaned_cases, dirty_ids = cleaner.filter_outliers(
        classic_cases=classic_cases,
        synthetic_cases=synthetic_cases,
        modern_cases=modern_cases,
        confidence_threshold=0.90,
        use_svm=True
    )
    
    print(f"\n✅ 动态清洗完成")
    print(f"   清洗后现代案例: {len(cleaned_cases)} 个")
    print(f"   识别出脏数据: {len(dirty_ids)} 个")
    if dirty_ids:
        print(f"\n   脏数据ID列表: {sorted(dirty_ids)}")

