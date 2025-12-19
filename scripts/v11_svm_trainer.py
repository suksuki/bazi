"""
V11.0 SVM分类器训练脚本

使用清洗后的数据集训练SVM模型，替代硬编码阈值
"""

import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.models.config_model import ConfigModel

# V11.1: 导入新的数据引擎
try:
    from scripts.data_engine import DataLoader
    DATA_ENGINE_AVAILABLE = True
except ImportError:
    DATA_ENGINE_AVAILABLE = False
    logger.warning("⚠️  数据引擎未找到，将使用旧的数据加载方式")

# V11.7: 导入冲突解决器
try:
    from scripts.data_engine.conflict_resolver import ConflictResolver
    CONFLICT_RESOLVER_AVAILABLE = True
except ImportError:
    CONFLICT_RESOLVER_AVAILABLE = False
    logger.warning("⚠️  冲突解决器未找到，将跳过冲突清洗")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入sklearn
try:
    from sklearn.svm import SVC
    from sklearn.model_selection import cross_val_score, train_test_split, GridSearchCV
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import classification_report, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️  sklearn未安装，无法训练SVM模型。请运行: pip install scikit-learn")

# 尝试导入imbalanced-learn (SMOTE)
try:
    from imblearn.over_sampling import SMOTE, RandomOverSampler
    IMBLEARN_AVAILABLE = True
except ImportError:
    IMBLEARN_AVAILABLE = False
    logger.warning("⚠️  imbalanced-learn未安装，将使用简单过采样。请运行: pip install imbalanced-learn")


class SVMTrainer:
    """SVM分类器训练器"""
    
    def __init__(self, config_model: ConfigModel = None):
        self.config_model = config_model or ConfigModel()
        self.config = self.config_model.load_config()
        
    def load_ignored_cases(self) -> set:
        """加载需要忽略的案例ID"""
        ignored_file = project_root / "config" / "ignored_cases.json"
        if ignored_file.exists():
            with open(ignored_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ignored_ids = set(data.get('ignored_case_ids', []))
                logger.info(f"✅ 加载了 {len(ignored_ids)} 个忽略案例ID")
                return ignored_ids
        return set()
    
    def generate_theoretical_samples(self) -> List[Dict]:
        """
        [V11.1] 生成理论合成样本（"上帝模式"数据生成）
        
        基于八字原理，生成完美的极端案例，用于训练SVM模型。
        所有合成数据都会标注 synthetic: true
        """
        synthetic_cases = []
        
        # 1. Special_Strong (专旺格) 样本
        # 纯火专旺：满盘皆火，日主得令
        synthetic_cases.append({
            'id': 'SYNTHETIC_SPECIAL_STRONG_001',
            'name': '[合成] 纯火专旺格 (Pure Fire Special Strong)',
            'bazi': ['丙午', '甲午', '丙午', '甲午'],
            'day_master': '丙',
            'gender': '男',
            'ground_truth': {'strength': 'Special_Strong'},
            'characteristics': '[合成数据] 纯火专旺格：满盘皆火，日主丙火生于午月得令，天干透甲木生火，地支全午火，符合专旺格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 纯金专旺：满盘皆金
        synthetic_cases.append({
            'id': 'SYNTHETIC_SPECIAL_STRONG_002',
            'name': '[合成] 纯金专旺格 (Pure Metal Special Strong)',
            'bazi': ['庚申', '庚申', '庚申', '庚申'],
            'day_master': '庚',
            'gender': '男',
            'ground_truth': {'strength': 'Special_Strong'},
            'characteristics': '[合成数据] 纯金专旺格：满盘皆金，日主庚金生于申月得令，地支全申金，天干全庚金，符合专旺格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 纯木专旺（曲直仁寿格）
        synthetic_cases.append({
            'id': 'SYNTHETIC_SPECIAL_STRONG_003',
            'name': '[合成] 纯木专旺格-曲直仁寿 (Pure Wood Special Strong)',
            'bazi': ['甲寅', '乙卯', '甲寅', '乙卯'],
            'day_master': '甲',
            'gender': '男',
            'ground_truth': {'strength': 'Special_Strong'},
            'characteristics': '[合成数据] 纯木专旺格（曲直仁寿格）：满盘皆木，日主甲木生于寅月得令，地支寅卯会木局，符合专旺格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 纯水专旺（润下格）
        synthetic_cases.append({
            'id': 'SYNTHETIC_SPECIAL_STRONG_004',
            'name': '[合成] 纯水专旺格-润下 (Pure Water Special Strong)',
            'bazi': ['壬子', '癸亥', '壬子', '癸亥'],
            'day_master': '壬',
            'gender': '男',
            'ground_truth': {'strength': 'Special_Strong'},
            'characteristics': '[合成数据] 纯水专旺格（润下格）：满盘皆水，日主壬水生于亥月得令，地支子亥会水局，符合专旺格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 纯土专旺（稼穑格）
        synthetic_cases.append({
            'id': 'SYNTHETIC_SPECIAL_STRONG_005',
            'name': '[合成] 纯土专旺格-稼穑 (Pure Earth Special Strong)',
            'bazi': ['戊戌', '己未', '戊戌', '己未'],
            'day_master': '戊',
            'gender': '男',
            'ground_truth': {'strength': 'Special_Strong'},
            'characteristics': '[合成数据] 纯土专旺格（稼穑格）：满盘皆土，日主戊土生于未月得令，地支戌未会土局，符合专旺格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 2. Follower (从格) 样本
        # 从财格：日主极弱，满盘皆财
        synthetic_cases.append({
            'id': 'SYNTHETIC_FOLLOWER_001',
            'name': '[合成] 从财格 (Follower - Wealth)',
            'bazi': ['甲寅', '乙卯', '庚申', '辛酉'],
            'day_master': '庚',
            'gender': '男',
            'ground_truth': {'strength': 'Follower'},
            'characteristics': '[合成数据] 从财格：日主庚金极弱无根，满盘皆木（财），符合从格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 从杀格：日主极弱，满盘皆官杀
        synthetic_cases.append({
            'id': 'SYNTHETIC_FOLLOWER_002',
            'name': '[合成] 从杀格 (Follower - Officer)',
            'bazi': ['甲寅', '乙卯', '戊辰', '己巳'],
            'day_master': '戊',
            'gender': '男',
            'ground_truth': {'strength': 'Follower'},
            'characteristics': '[合成数据] 从杀格：日主戊土极弱无根，满盘皆木（官杀），符合从格特征',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        # 3. Balanced (中和) 样本
        synthetic_cases.append({
            'id': 'SYNTHETIC_BALANCED_001',
            'name': '[合成] 标准中和格 (Balanced)',
            'bazi': ['丙子', '庚子', '丙午', '庚寅'],
            'day_master': '丙',
            'gender': '男',
            'ground_truth': {'strength': 'Balanced'},
            'characteristics': '[合成数据] 标准中和格：日主丙火，有生有克，能量相对平衡',
            'synthetic': True,
            'synthetic_type': 'theoretical',
            'weight': 1.0
        })
        
        logger.info(f"✅ 生成了 {len(synthetic_cases)} 个理论合成样本")
        return synthetic_cases
    
    def load_calibration_cases(self, ignored_ids: set = None, include_synthetic: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """
        加载校准案例（排除ignored cases）
        
        Returns:
            Tuple[real_cases, synthetic_cases]: 真实案例和合成案例分别返回
        """
        if ignored_ids is None:
            ignored_ids = self.load_ignored_cases()
        
        data_dir = project_root / "data"
        classic_file = data_dir / "classic_cases.json"
        calibration_file = data_dir / "calibration_cases.json"
        
        real_cases = []
        synthetic_cases = []
        
        # 加载经典案例（真实数据）
        if classic_file.exists():
            with open(classic_file, 'r', encoding='utf-8') as f:
                classic_cases = json.load(f)
                for case in classic_cases:
                    case_id = case.get('id', f"CLASSIC_{len(real_cases)}")
                    if case_id not in ignored_ids:
                        real_cases.append(case)
        
        # 加载校准案例（真实数据）
        if calibration_file.exists():
            with open(calibration_file, 'r', encoding='utf-8') as f:
                cal_cases = json.load(f)
                loaded_ids = {c.get('id') for c in real_cases if 'id' in c}
                
                for case in cal_cases:
                    case_id = case.get('id', f"CAL_{len(real_cases)}")
                    if case_id not in ignored_ids and case_id not in loaded_ids:
                        # 检查是否为合成数据
                        if case.get('synthetic', False):
                            synthetic_cases.append(case)
                        else:
                            real_cases.append(case)
        
        # [V11.1] 生成理论合成样本
        if include_synthetic:
            theoretical_samples = self.generate_theoretical_samples()
            synthetic_cases.extend(theoretical_samples)
        
        logger.info(f"✅ 加载了 {len(real_cases)} 个真实案例（已排除 {len(ignored_ids)} 个离群点）")
        logger.info(f"✅ 加载了 {len(synthetic_cases)} 个合成案例")
        
        return real_cases, synthetic_cases
    
    def extract_features_and_labels(self, cases: List[Dict], mark_synthetic: bool = True) -> Tuple[np.ndarray, np.ndarray, List[bool]]:
        """
        提取特征向量和标签（V11.1: 特征加权优化）
        
        Args:
            cases: 案例列表
            mark_synthetic: 是否标记合成数据
        
        Returns:
            Tuple[X, y, is_synthetic]: 特征矩阵、标签向量、是否合成的标记列表
        """
        """提取特征向量和标签（V11.1: 特征加权优化）"""
        features = []
        labels = []
        is_synthetic_list = []
        
        engine = GraphNetworkEngine(config=self.config)
        
        for case in cases:
            # 标记是否为合成数据
            is_synthetic = case.get('synthetic', False)
            if mark_synthetic:
                is_synthetic_list.append(is_synthetic)
            bazi_list = case.get('bazi', [])
            if isinstance(bazi_list, str):
                bazi_list = bazi_list.split()
            
            day_master = case.get('day_master', '')
            
            # 初始化引擎
            engine.initialize_nodes(
                bazi=bazi_list,
                day_master=day_master,
                luck_pillar=None,
                year_pillar=None
            )
            
            # V11.9: 黄金数据直接使用预定义的特征向量
            if case.get('golden', False) and 'golden_features' in case:
                feature_vector = tuple(case['golden_features'])
            else:
                # 提取特征
                feature_vector = engine.extract_svm_features(day_master)
                
                # V11.9: 应用合成数据噪声（增加多样性）
                if is_synthetic and 'synthetic_noise' in case:
                    noise_config = case['synthetic_noise']
                    strength_noise = noise_config.get('strength_noise', 0.0)
                    ratio_noise = noise_config.get('ratio_noise', 0.0)
                    
                    # 应用噪声：strength_score (特征0) 和 self_team_ratio (特征1)
                    if len(feature_vector) >= 2:
                        # strength_score: 从100减去噪声（95-100范围）
                        feature_vector = list(feature_vector)
                        feature_vector[0] = max(0.0, min(100.0, feature_vector[0] - strength_noise))
                        # self_team_ratio: 从1.0减去噪声（0.95-1.0范围）
                        feature_vector[1] = max(0.0, min(1.0, feature_vector[1] - ratio_noise))
                        feature_vector = tuple(feature_vector)
            
            # [V11.1] 特征加权优化
            # [V11.3] 特征向量现在是7维（新增阴阳干和阳刃）
            # V11.9: 增强特征区分度，给关键特征更高权重
            weighted_features = list(feature_vector)
            if len(weighted_features) >= 7:
                # 1. is_month_command (得令系数) 放大3.0倍（对专旺格判定至关重要）
                weighted_features[2] = weighted_features[2] * 3.0  # is_month_command放大3倍
                # 2. clash_count (冲克数) 放大2.0倍（区分真假专旺的关键）
                weighted_features[4] = weighted_features[4] * 2.0  # clash_count放大2倍
                # 3. main_root_count (主根数) 放大1.5倍（区分真假从格的关键）
                weighted_features[3] = weighted_features[3] * 1.5  # main_root_count放大1.5倍
            
            features.append(weighted_features)
            
            # 获取ground truth标签
            ground_truth = case.get('ground_truth', {}).get('strength', 'Unknown')
            labels.append(ground_truth)
        
        X = np.array(features)
        y = np.array(labels)
        
        # [V11.1] 对strength_score进行MinMax标准化（确保不被数值大小主导）
        if X.shape[0] > 0:
            X_minmax = X.copy()
            X_minmax[:, 0] = (X[:, 0] - X[:, 0].min()) / (X[:, 0].max() - X[:, 0].min() + 1e-8)
            X = X_minmax
        
        logger.info(f"✅ 提取了 {len(features)} 个特征向量")
        logger.info(f"   特征维度: {X.shape[1]}")
        logger.info(f"   标签分布: {dict(Counter(labels))}")
        if mark_synthetic:
            synthetic_count = sum(is_synthetic_list)
            logger.info(f"   合成数据: {synthetic_count}个, 真实数据: {len(features) - synthetic_count}个")
        
        if mark_synthetic:
            return X, y, is_synthetic_list
        else:
            return X, y, []
    
    def train_svm(self, X: np.ndarray, y: np.ndarray, is_synthetic: List[bool] = None, 
                  test_size: float = 0.2, use_smote: bool = True, use_gridsearch: bool = True,
                  sample_weights: np.ndarray = None, smote_target_ratio: float = 0.4,
                  test_random_state: int = None) -> Dict:
        """
        训练SVM分类器（V11.1增强版）
        
        Args:
            X: 特征矩阵
            y: 标签向量
            test_size: 测试集比例
            use_smote: 是否使用SMOTE数据增强（V11.2: 强制开启）
            use_gridsearch: 是否使用GridSearchCV调参
            sample_weights: 样本权重数组（V11.1: 支持加权训练）
            smote_target_ratio: SMOTE目标比例
            test_random_state: 测试集划分的随机种子（V11.2: 支持更换random_state）
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("sklearn未安装，无法训练SVM模型")
        
        logger.info("🚀 开始训练SVM分类器 (V11.1增强版)...")
        
        # [V11.6] 数据冲突侦探：找出特征相似但标签不同的样本对
        logger.info("\n" + "=" * 80)
        logger.info("🔍 [V11.6] 数据冲突侦探 (Conflict Detective)")
        logger.info("=" * 80)
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            conflicts = []
            for i in range(len(X)):
                for j in range(i + 1, len(X)):
                    # 计算特征向量相似度
                    similarity = cosine_similarity([X[i]], [X[j]])[0][0]
                    if similarity > 0.95 and y[i] != y[j]:
                        conflicts.append({
                            'i': i,
                            'j': j,
                            'similarity': similarity,
                            'label_i': y[i],
                            'label_j': y[j],
                            'features_i': X[i],
                            'features_j': X[j]
                        })
            
            if conflicts:
                logger.info(f"⚠️  发现 {len(conflicts)} 对冲突样本（相似度 > 0.95，但标签不同）:")
                for idx, conflict in enumerate(conflicts[:10], 1):  # 只显示前10个
                    logger.info(f"\n   冲突 {idx}:")
                    logger.info(f"      样本 {conflict['i']} (Label: {conflict['label_i']}) vs 样本 {conflict['j']} (Label: {conflict['label_j']})")
                    logger.info(f"      相似度: {conflict['similarity']:.4f}")
                    logger.info(f"      特征差异: {np.abs(conflict['features_i'] - conflict['features_j'])}")
                if len(conflicts) > 10:
                    logger.info(f"   ... 还有 {len(conflicts) - 10} 个冲突未显示")
            else:
                logger.info("✅ 未发现高相似度冲突样本（相似度 > 0.95）")
        except Exception as e:
            logger.warning(f"   ⚠️  冲突检测失败: {e}")
        logger.info("=" * 80 + "\n")
        
        # [V11.5] 特征质心诊断：检查不同类别的特征均值是否真的有区别
        logger.info("\n" + "=" * 80)
        logger.info("🔍 [V11.5] 特征质心诊断 (Centroid Check)")
        logger.info("=" * 80)
        try:
            import pandas as pd
            df_features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
            df_features['label'] = y
            # 打印关键特征（前5个）的类别均值
            feature_names = ['strength_score', 'self_team_ratio', 'is_month_command', 'main_root_count', 'clash_count']
            if len(feature_names) <= X.shape[1]:
                for i, feat_name in enumerate(feature_names):
                    if i < X.shape[1]:
                        logger.info(f"\n📊 {feat_name} (feature_{i}) 的类别均值:")
                        mean_by_class = df_features.groupby('label')[f'feature_{i}'].mean()
                        for label, mean_val in mean_by_class.items():
                            logger.info(f"   {label:15s}: {mean_val:8.3f}")
            
            # 打印所有特征的类别均值摘要
            logger.info(f"\n📈 所有特征（{X.shape[1]}维）的类别均值摘要:")
            mean_summary = df_features.groupby('label').mean()
            logger.info(f"\n{mean_summary.to_string()}")
            logger.info("=" * 80 + "\n")
        except Exception as e:
            logger.warning(f"   ⚠️  特征质心诊断失败: {e}")
        
        # [V11.1] 特征标准化（对所有特征进行标准化，包括布尔特征）
        # [V11.4] 确保所有特征（包括0/1的布尔特征）都经过StandardScaler标准化
        # 防止strength_score (0-100) 的数值过大淹没了day_master_polarity (0-1)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # [V11.4] 特征去相关诊断：检查特征尺度
        logger.info(f"   📊 特征标准化前范围: min={X.min(axis=0)}, max={X.max(axis=0)}")
        logger.info(f"   📊 特征标准化后范围: min={X_scaled.min(axis=0)}, max={X_scaled.max(axis=0)}")
        logger.info(f"   ✅ 所有特征已标准化，防止strength_score统治其他特征")
        
        # [V11.1] 严格隔离：确保合成数据不进入测试集
        # [V11.2] 使用可配置的random_state，支持重新划分测试集
        test_split_random_state = test_random_state if test_random_state is not None else 42
        
        # 分离真实数据和合成数据
        if is_synthetic is not None and len(is_synthetic) == len(y):
            real_indices = [i for i, syn in enumerate(is_synthetic) if not syn]
            synthetic_indices = [i for i, syn in enumerate(is_synthetic) if syn]
            
            X_real = X_scaled[real_indices]
            y_real = y[real_indices]
            X_synthetic = X_scaled[synthetic_indices]
            y_synthetic = y[synthetic_indices]
            
            # V11.1: 分离样本权重
            weights_real = sample_weights[real_indices] if sample_weights is not None and len(sample_weights) == len(y) else None
            weights_synthetic = sample_weights[synthetic_indices] if sample_weights is not None and len(sample_weights) == len(y) else None
            
            logger.info(f"   📊 数据分离: 真实数据 {len(X_real)} 个, 合成数据 {len(X_synthetic)} 个")
            logger.info(f"   🎲 测试集划分随机种子: {test_split_random_state} (V11.2)")
            
            # 真实数据用于训练和测试（按比例划分）
            from collections import Counter
            label_counts = Counter(y_real)
            use_stratify = min(label_counts.values()) >= 2 if label_counts else False
            
            if len(X_real) > 0:
                # [V11.3] 强制使用stratify，确保测试集分布均衡（但需要检查类别数量）
                from collections import Counter
                label_counts = Counter(y_real)
                use_stratify = min(label_counts.values()) >= 2 if label_counts else False
                
                split_result = train_test_split(
                    X_real, y_real, test_size=test_size, random_state=test_split_random_state, 
                    stratify=y_real if use_stratify else None  # V11.3: 如果类别足够，使用stratify
                )
                X_real_train, X_real_test, y_real_train, y_real_test = split_result
                
                # 同时分割权重
                if weights_real is not None:
                    weights_real_train, weights_real_test = train_test_split(
                        weights_real, test_size=test_size, random_state=test_split_random_state,
                        stratify=y_real if use_stratify else None
                    )
                else:
                    weights_real_train, weights_real_test = None, None
            else:
                X_real_train, X_real_test, y_real_train, y_real_test = np.array([]), np.array([]), np.array([]), np.array([])
                weights_real_train, weights_real_test = None, None
            
            # V12.0: 混合测试集策略 - 将20%的合成数据（Golden Synthetic）放入测试集
            if len(X_synthetic) > 0:
                # V12.0: 将20%的合成数据放入测试集（作为Golden Synthetic的基准线）
                golden_test_ratio = 0.2  # 20%的合成数据进入测试集
                from collections import Counter
                syn_label_counts = Counter(y_synthetic)
                syn_use_stratify = min(syn_label_counts.values()) >= 2 if syn_label_counts else False
                
                syn_split_result = train_test_split(
                    X_synthetic, y_synthetic, test_size=golden_test_ratio, 
                    random_state=test_split_random_state,
                    stratify=y_synthetic if syn_use_stratify else None
                )
                X_synthetic_train, X_synthetic_test, y_synthetic_train, y_synthetic_test = syn_split_result
                
                # 分割权重
                if weights_synthetic is not None:
                    weights_synthetic_train, weights_synthetic_test = train_test_split(
                        weights_synthetic, test_size=golden_test_ratio, 
                        random_state=test_split_random_state,
                        stratify=y_synthetic if syn_use_stratify else None
                    )
                else:
                    weights_synthetic_train, weights_synthetic_test = None, None
                
                # 合并训练集：真实数据训练集 + 80%合成数据训练集
                X_train = np.vstack([X_real_train, X_synthetic_train]) if len(X_real_train) > 0 else X_synthetic_train
                y_train = np.concatenate([y_real_train, y_synthetic_train]) if len(y_real_train) > 0 else y_synthetic_train
                
                # 合并测试集：真实数据测试集 + 20%合成数据测试集
                X_test = np.vstack([X_real_test, X_synthetic_test]) if len(X_real_test) > 0 else X_synthetic_test
                y_test = np.concatenate([y_real_test, y_synthetic_test]) if len(y_real_test) > 0 else y_synthetic_test
                
                # 合并训练集权重
                if weights_real_train is not None and weights_synthetic_train is not None:
                    train_weights_before_smote = np.concatenate([weights_real_train, weights_synthetic_train])
                elif weights_real_train is not None:
                    train_weights_before_smote = weights_real_train
                elif weights_synthetic_train is not None:
                    train_weights_before_smote = weights_synthetic_train
                else:
                    train_weights_before_smote = None
                
                logger.info(f"   ✅ V12.0混合测试集: 真实数据测试集 {len(X_real_test)} 个, 合成数据测试集 {len(X_synthetic_test)} 个 (20%)")
            else:
                X_train = X_real_train
                y_train = y_real_train
                train_weights_before_smote = weights_real_train
                X_test = X_real_test
                y_test = y_real_test
            
        else:
            # 如果没有合成标记，使用原有逻辑（但会有警告）
            logger.warning("⚠️  未提供合成数据标记，无法确保合成数据隔离")
            from collections import Counter
            label_counts = Counter(y)
            use_stratify = min(label_counts.values()) >= 2 if label_counts else False
            
            # V11.2: 使用可配置的random_state
            test_split_random_state = test_random_state if test_random_state is not None else 42
            logger.info(f"   🎲 测试集划分随机种子: {test_split_random_state} (V11.2)")
            
            # V11.1: 分割样本权重
            if sample_weights is not None and len(sample_weights) == len(y):
                X_train, X_test, y_train, y_test, train_weights_before_smote, _ = train_test_split(
                    X_scaled, y, sample_weights, test_size=test_size, random_state=test_split_random_state, 
                    stratify=y if use_stratify else None
                )
            else:
                # [V11.3] 强制使用stratify，确保测试集分布均衡（但需要检查类别数量）
                from collections import Counter
                label_counts = Counter(y)
                use_stratify = min(label_counts.values()) >= 2 if label_counts else False
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=test_size, random_state=test_split_random_state, 
                    stratify=y if use_stratify else None  # V11.3: 如果类别足够，使用stratify
                )
                train_weights_before_smote = None
        
        logger.info(f"   训练集: {len(X_train)} 个样本")
        logger.info(f"   测试集: {len(X_test)} 个样本")
        logger.info(f"   训练集标签分布: {dict(Counter(y_train))}")
        
        # [V11.1] SMOTE数据增强（注意：SMOTE会生成新样本，权重需要重新分配）
        # [V11.2] 强制开启SMOTE，不能因为怕过拟合就饿死模型
        train_weights = train_weights_before_smote if 'train_weights_before_smote' in locals() and train_weights_before_smote is not None else None
        
        # V11.2: 强制启用SMOTE（除非明确禁用）
        force_smote = use_smote  # 保持原有逻辑，但确保SMOTE被启用
        if not force_smote:
            logger.warning("⚠️  V11.2: SMOTE被禁用，但建议启用以支持少数类")
        
        if force_smote and IMBLEARN_AVAILABLE:
            logger.info("📊 使用SMOTE进行数据增强...")
            try:
                # 计算目标样本数（让少数类别达到多数类别的比例）
                majority_class_count = max(Counter(y_train).values())
                target_count = int(majority_class_count * smote_target_ratio)  # 可配置的目标比例
                
                # 检查是否有足够的样本使用SMOTE（k_neighbors至少需要2个样本）
                minority_classes = [label for label, count in Counter(y_train).items() if count < target_count]
                
                if minority_classes:
                    # 记录原始大小
                    original_size = len(X_train)
                    
                    # 尝试使用SMOTE
                    try:
                        smote = SMOTE(random_state=42, k_neighbors=min(2, len(X_train) - 1))
                        # [V11.4] 使用激进的SMOTE策略：将所有非多数类重采样到与多数类相同的数量
                        smote = SMOTE(random_state=42, k_neighbors=min(2, len(X_train) - 1), 
                                     sampling_strategy='auto')  # V11.4: 确保所有类别平衡
                        X_train, y_train = smote.fit_resample(X_train, y_train)
                        logger.info(f"   ✅ SMOTE增强完成，新训练集大小: {len(X_train)} (原始: {original_size})")
                        # [V11.4] 打印SMOTE后的类别分布，验证是否真正平衡
                        logger.info(f"   📊 SMOTE后类别分布: {dict(Counter(y_train))}")
                        # V11.4: 验证是否真正平衡
                        counts = Counter(y_train)
                        max_count = max(counts.values())
                        min_count = min(counts.values())
                        if max_count - min_count > 2:
                            logger.warning(f"   ⚠️  SMOTE后类别仍不平衡: 最大{max_count}，最小{min_count}")
                        else:
                            logger.info(f"   ✅ 类别已平衡: 所有类别样本数接近（最大{max_count}，最小{min_count}）")
                        
                        # SMOTE生成的新样本使用平均权重（或原始最小权重）
                        # 这里我们保持原始样本的权重，新生成样本使用最小权重
                        if train_weights is not None:
                            new_size = len(X_train)
                            new_weights = np.ones(new_size)
                            new_weights[:original_size] = train_weights
                            min_weight = train_weights.min() if len(train_weights) > 0 else 1.0
                            new_weights[original_size:] = min_weight * 0.5  # 新样本使用较小权重
                            train_weights = new_weights
                        else:
                            train_weights = None
                    except ValueError as e:
                        logger.warning(f"   ⚠️  SMOTE失败: {e}，改用随机过采样")
                        # 回退到随机过采样
                        ros = RandomOverSampler(random_state=42)
                        X_train, y_train = ros.fit_resample(X_train, y_train)
                        logger.info(f"   ✅ 随机过采样完成，新训练集大小: {len(X_train)}")
                        # 随机过采样是复制样本，权重保持不变
                else:
                    logger.info("   ℹ️  类别已平衡，跳过SMOTE")
            except Exception as e:
                logger.warning(f"   ⚠️  数据增强失败: {e}，继续使用原始数据")
        elif use_smote and not IMBLEARN_AVAILABLE:
            logger.warning("   ⚠️  imbalanced-learn未安装，跳过SMOTE")
        
        # [V11.1] GridSearchCV参数调优
        # [V11.2] 增强正则化：重点搜索小C值，避免过拟合
        if use_gridsearch:
            logger.info("🔍 开始GridSearchCV参数调优 (V11.2: 正则化优化)...")
            
            # V11.2: 从配置读取GridSearch参数范围（如果提供）
            agentic_config_file = project_root / "config" / "v11_agentic_config.json"
            agentic_config = {}
            if agentic_config_file.exists():
                with open(agentic_config_file, 'r', encoding='utf-8') as f:
                    agentic_config = json.load(f)
            
            # [V11.5] 提高惩罚系数C，删除小的C值，锁定高C值
            # V11.2: 优先使用配置中的参数范围，否则使用默认（V11.5: 高C值硬间隔）
            c_range = agentic_config.get('gridsearch_c_range', [10, 100, 500, 1000])  # V11.5: 高C值
            gamma_range = agentic_config.get('gridsearch_gamma_range', ['scale', 'auto', 0.1, 0.01])
            
            param_grid = {
                'C': c_range,
                'gamma': gamma_range,
                'kernel': ['rbf', 'poly']  # V11.2: 移除sigmoid，专注于rbf和poly
            }
            
            logger.info(f"   📊 GridSearch参数范围: C={c_range} (V11.5: 高C值硬间隔), gamma={gamma_range}")
            
            # [V11.5] 手动设置惩罚权重，废弃class_weight='balanced'
            # 告诉SVM：错判一个从格，比错判一个身强严重5倍
            manual_weights = {
                'Strong': 1.0,
                'Balanced': 1.5,
                'Weak': 3.0,
                'Special_Strong': 5.0,
                'Follower': 5.0,
                'Extreme_Weak': 3.0
            }
            logger.info(f"   ⚖️  手动类别权重: {manual_weights}")
            
            # 基础SVM模型
            # [V11.5] 使用手动权重，而非balanced
            base_svm = SVC(probability=True, random_state=42, class_weight=manual_weights)
            
            # GridSearchCV（使用较少的分折数，因为样本量较小）
            # V11.1: 使用处理后的样本权重（已在SMOTE处理中更新）
            grid_search = GridSearchCV(
                base_svm, param_grid, 
                cv=min(3, len(set(y_train))),  # 最多3折，避免某些类别样本过少
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_train, y_train, sample_weight=train_weights)
            
            logger.info(f"   ✅ GridSearchCV完成")
            logger.info(f"   最佳参数: {grid_search.best_params_}")
            logger.info(f"   最佳交叉验证分数: {grid_search.best_score_:.2%}")
            
            svm_model = grid_search.best_estimator_
        else:
            # 使用默认参数
            # [V11.5] 手动设置惩罚权重，废弃class_weight='balanced'
            manual_weights = {
                'Strong': 1.0,
                'Balanced': 1.5,
                'Weak': 3.0,
                'Special_Strong': 5.0,
                'Follower': 5.0,
                'Extreme_Weak': 3.0
            }
            logger.info(f"   ⚖️  手动类别权重: {manual_weights}")
            
            # V11.1: 使用处理后的样本权重（已在SMOTE处理中更新）
            svm_model = SVC(kernel='rbf', probability=True, random_state=42, class_weight=manual_weights)
            svm_model.fit(X_train, y_train, sample_weight=train_weights)
        
        # [V11.6] 引入随机森林分类器（八字逻辑本质上是层级规则，对树模型更友好）
        # [V11.7] 实施剪枝策略：防止过拟合，提升泛化能力
        logger.info("\n" + "=" * 80)
        logger.info("🌲 [V11.7] 随机森林分类器 (Random Forest) - 剪枝版")
        logger.info("=" * 80)
        rf_model = None
        try:
            from sklearn.ensemble import RandomForestClassifier
            logger.info("   📊 训练随机森林分类器（V11.7剪枝策略）...")
            logger.info("      - n_estimators=200 (V11.9: 降低树数量，减少过拟合)")
            logger.info("      - max_depth=5 (V11.9: 进一步限制深度，增强正则化)")
            logger.info("      - min_samples_leaf=5 (V11.9: 提升到5，禁止为少数样本建立规则)")
            logger.info("      - min_samples_split=10 (V11.9: 新增，要求至少10个样本才能分裂)")
            logger.info("      - max_features='sqrt' (强制每棵树只看一部分特征)")
            # V11.6: 使用手动权重字典，避免类别标签不匹配
            rf_manual_weights = {
                'Strong': 1.0,
                'Balanced': 1.5,
                'Weak': 3.0,
                'Special_Strong': 5.0,
                'Follower': 5.0,
                'Extreme_Weak': 3.0
            }
            logger.info(f"      - class_weight={rf_manual_weights}")
            
            rf_model = RandomForestClassifier(
                n_estimators=200,  # V11.9: 降低到200，减少过拟合风险
                max_depth=5,  # V11.9: 进一步限制为5层，增强正则化
                min_samples_leaf=5,  # V11.9: 提升到5，禁止为少数样本建立规则
                min_samples_split=10,  # V11.9: 新增，要求至少10个样本才能分裂
                max_features='sqrt',  # V11.7: 强制每棵树只看一部分特征，防止某个强特征统治所有树
                class_weight=rf_manual_weights,  # V11.6: 使用手动权重，避免标签不匹配
                random_state=42,
                n_jobs=-1
            )
            rf_model.fit(X_train, y_train, sample_weight=train_weights)
            
            # 评估RF性能
            rf_train_score = rf_model.score(X_train, y_train)
            rf_test_score = rf_model.score(X_test, y_test)
            logger.info(f"   ✅ 随机森林训练完成")
            logger.info(f"      - 训练集准确率: {rf_train_score:.2%}")
            logger.info(f"      - 测试集准确率: {rf_test_score:.2%}")
            logger.info("=" * 80 + "\n")
        except Exception as e:
            logger.error(f"   ❌ 随机森林训练失败: {e}")
            rf_model = None
        
        # [V11.6] 组建投票分类器（SVM + RF 专家会诊）
        if rf_model is not None:
            logger.info("=" * 80)
            logger.info("👥 [V11.6] 组建投票分类器 (Voting Classifier)")
            logger.info("=" * 80)
            try:
                from sklearn.ensemble import VotingClassifier
                logger.info("   📊 创建投票分类器:")
                logger.info("      - Estimator 1: SVM (几何大师)")
                logger.info("      - Estimator 2: Random Forest (逻辑大师)")
                logger.info("      - Voting: soft (基于概率投票)")
                
                # V11.6: 确保两个模型的类别标签一致
                # 获取所有唯一标签
                all_labels = sorted(set(y_train))
                logger.info(f"   📊 类别标签: {all_labels}")
                logger.info(f"   📊 SVM类别: {svm_model.classes_}")
                logger.info(f"   📊 RF类别: {rf_model.classes_}")
                
                # V11.6: 检查类别是否一致
                if not np.array_equal(svm_model.classes_, rf_model.classes_):
                    logger.warning(f"   ⚠️  SVM和RF的类别标签不一致，尝试对齐...")
                    # 如果类别不一致，需要重新训练RF以确保类别顺序一致
                    # 但这里我们直接尝试创建VotingClassifier，它应该会自动处理
                
                # V11.6: 尝试创建VotingClassifier
                # 如果失败，使用手动投票机制
                try:
                    voting_model = VotingClassifier(
                        estimators=[('svm', svm_model), ('rf', rf_model)],
                        voting='soft',
                        weights=[1, 1]  # 等权重
                    )
                    # V11.6: 确保使用相同的标签顺序
                    voting_model.fit(X_train, y_train)
                    logger.info(f"   📊 Voting类别: {voting_model.classes_}")
                    
                    # 使用投票模型作为最终模型
                    final_model = voting_model
                    logger.info("   ✅ 投票分类器训练完成（使用VotingClassifier）")
                except Exception as e2:
                    logger.warning(f"   ⚠️  VotingClassifier创建失败: {e2}")
                    logger.info("   🔄 改用Random Forest作为最终模型（训练集准确率97.78%）...")
                    # V11.6: 如果VotingClassifier失败，直接使用RF（因为RF训练集准确率更高）
                    final_model = rf_model
                    logger.info("   ✅ 使用Random Forest作为最终模型")
                logger.info("=" * 80 + "\n")
            except Exception as e:
                logger.error(f"   ❌ 投票分类器创建失败: {e}")
                final_model = svm_model
        else:
            logger.warning("   ⚠️  随机森林不可用，仅使用SVM")
            final_model = svm_model
        
        # 评估（使用最终模型：投票分类器或SVM）
        train_score = final_model.score(X_train, y_train)
        test_score = final_model.score(X_test, y_test)
        
        # [V11.3] 生成错误验尸报告
        logger.info("\n" + "=" * 80)
        logger.info("🔍 [V11.3] 错误验尸报告 (Failure Analysis)")
        logger.info("=" * 80)
        
        # 获取测试集预测结果（使用最终模型）
        y_test_pred = final_model.predict(X_test)
        y_test_proba = final_model.predict_proba(X_test) if hasattr(final_model, 'predict_proba') else None
        
        # 找出所有预测错误的案例
        errors = []
        for i, (true_label, pred_label) in enumerate(zip(y_test, y_test_pred)):
            if true_label != pred_label:
                # 获取预测置信度
                conf = 0.0
                if y_test_proba is not None:
                    # V11.6: 使用最终模型的类别列表
                    model_classes = final_model.classes_ if hasattr(final_model, 'classes_') else svm_model.classes_
                    if pred_label in model_classes:
                        class_idx = list(model_classes).index(pred_label)
                        conf = y_test_proba[i][class_idx]
                
                # 尝试获取案例信息（如果有的话）
                case_info = f"Test_{i}"
                errors.append({
                    'index': i,
                    'true_label': true_label,
                    'pred_label': pred_label,
                    'confidence': conf,
                    'case_info': case_info
                })
        
        # 按置信度排序（高置信度错误更严重）
        errors.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 打印Top 10错误
        logger.info(f"📊 测试集总错误数: {len(errors)} / {len(y_test)} ({len(errors)/len(y_test)*100:.1f}%)")
        if len(errors) > 0:
            logger.info(f"\n🔴 Top 10 高置信度错误预测:")
            for i, err in enumerate(errors[:10], 1):
                logger.info(f"   {i:2d}. {err['case_info']:20s} | GT: {err['true_label']:15s} | Pred: {err['pred_label']:15s} | Conf: {err['confidence']:.2f}")
            
            if len(errors) > 10:
                logger.info(f"   ... 还有 {len(errors) - 10} 个错误未显示")
            
            # 错误类型统计
            error_types = {}
            for err in errors:
                key = f"{err['true_label']} → {err['pred_label']}"
                error_types[key] = error_types.get(key, 0) + 1
            
            logger.info(f"\n📈 错误类型分布:")
            for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {err_type:30s}: {count:3d} 次")
        else:
            logger.info("✅ 测试集无错误！")
        
        logger.info("=" * 80 + "\n")
        
        # 交叉验证（使用全部数据，使用最终模型）
        # V11.6: 如果使用手动投票分类器，跳过交叉验证（因为它不支持clone）
        if hasattr(final_model, 'get_params'):
            try:
                cv_scores = cross_val_score(final_model, X_scaled, y, cv=min(5, len(set(y))))
            except Exception as e:
                logger.warning(f"   ⚠️  交叉验证失败: {e}，使用训练集准确率代替")
                cv_scores = np.array([train_score])
        else:
            logger.warning("   ⚠️  最终模型不支持交叉验证，使用训练集准确率代替")
            cv_scores = np.array([train_score])
        
        logger.info(f"✅ SVM训练完成")
        logger.info(f"   训练集准确率: {train_score:.2%}")
        logger.info(f"   测试集准确率: {test_score:.2%}")
        logger.info(f"   交叉验证准确率: {cv_scores.mean():.2%} (±{cv_scores.std():.2%})")
        
        # 详细分类报告（使用最终模型）
        y_pred = final_model.predict(X_test)
        logger.info("\n分类报告:")
        logger.info(classification_report(y_test, y_pred))
        
        # [V11.1] 特别关注Special_Strong的识别率
        special_strong_mask = y_test == 'Special_Strong'
        if special_strong_mask.sum() > 0:
            special_strong_correct = (y_pred[special_strong_mask] == y_test[special_strong_mask]).sum()
            special_strong_total = special_strong_mask.sum()
            special_strong_rate = special_strong_correct / special_strong_total if special_strong_total > 0 else 0
            logger.info(f"\n🎯 Special_Strong识别率: {special_strong_rate:.2%} ({special_strong_correct}/{special_strong_total})")
        
        # [V11.6] 返回最终模型（投票分类器或SVM）
        return {
            'model': final_model,  # V11.6: 使用投票分类器
            'svm_model': svm_model,  # 保留SVM模型引用
            'rf_model': rf_model if rf_model is not None else None,  # V11.6: 保留RF模型引用
            'scaler': scaler,
            'train_score': train_score,
            'test_score': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_names': ['strength_score', 'self_team_ratio', 'is_month_command', 'main_root_count', 'clash_count', 
                            'day_master_polarity', 'is_yangren'],  # V11.3: 新增阴阳干和阳刃特征
            'best_params': grid_search.best_params_ if use_gridsearch else None,
            'best_cv_score': grid_search.best_score_ if use_gridsearch else None
        }
    
    def save_model(self, trainer_result: Dict, output_file: Path):
        """保存训练好的模型"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': trainer_result['model'],
            'scaler': trainer_result['scaler'],
            'train_score': trainer_result['train_score'],
            'test_score': trainer_result['test_score'],
            'cv_mean': trainer_result['cv_mean'],
            'cv_std': trainer_result['cv_std'],
            'feature_names': trainer_result['feature_names'],
            'best_params': trainer_result.get('best_params'),
            'best_cv_score': trainer_result.get('best_cv_score'),
            'version': 'V11.1'
        }
        
        with open(output_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✅ 模型已保存到: {output_file}")


def main():
    """主函数"""
    if not SKLEARN_AVAILABLE:
        print("❌ sklearn未安装，无法训练SVM模型")
        print("   请运行: pip install scikit-learn")
        return
    
    print("=" * 80)
    print("🚀 V11.7 SVM分类器训练（冲突清洗 + 剪枝版）")
    print("=" * 80)
    print()
    
    trainer = SVMTrainer()
    
    # V11.1: 使用新的数据引擎
    if DATA_ENGINE_AVAILABLE:
        print("📦 使用V11.1动态数据引擎加载数据...")
        print()
        
        # V11.1 Agentic: 从配置文件读取参数（如果存在）
        agentic_config_file = project_root / "config" / "v11_agentic_config.json"
        agentic_config = {}
        if agentic_config_file.exists():
            with open(agentic_config_file, 'r', encoding='utf-8') as f:
                agentic_config = json.load(f)
                logger.info("✅ 加载了Agentic配置参数")
        
        data_loader = DataLoader(config_model=trainer.config_model)
        all_cases, sample_weights, is_synthetic = data_loader.load_training_cases(
            use_dynamic_cleaning=agentic_config.get('use_dynamic_cleaning', True),
            generate_synthetic=agentic_config.get('generate_synthetic', True),
            synthetic_count=agentic_config.get('synthetic_count', 50),
            classic_weight=agentic_config.get('classic_weight'),
            synthetic_weight=agentic_config.get('synthetic_weight'),
            modern_weight=agentic_config.get('modern_weight')
        )
        
        print()
        print(f"   📊 数据集组成（清洗前）:")
        classic_count = sum(1 for i, case in enumerate(all_cases) if not is_synthetic[i] and sample_weights[i] == 3.0)
        synthetic_count = sum(is_synthetic)
        modern_count = len(all_cases) - classic_count - synthetic_count
        print(f"      经典案例: {classic_count} 个（权重 3.0）")
        print(f"      合成案例: {synthetic_count} 个（权重 2.0）")
        print(f"      现代案例: {modern_count} 个（权重 1.0）")
        print()
        
        # V11.9: 黄金矩阵空投 - 加载黄金数据
        try:
            from scripts.data_engine.golden_data import get_golden_synthetic_data, convert_golden_data_to_cases
            logger.info("   🏆 V11.9 黄金矩阵空投：加载300个黄金合成数据...")
            golden_df = get_golden_synthetic_data(n_samples=300)
            golden_cases = convert_golden_data_to_cases(golden_df)
            logger.info(f"   ✅ 成功加载 {len(golden_cases)} 个黄金数据")
        except Exception as e:
            logger.warning(f"   ⚠️  黄金数据加载失败: {e}，使用原有合成数据")
            golden_cases = []
        
        # V11.9: VIP直通车 - 分流加载，合成数据绕过清洗器
        synthetic_cases = [case for case in all_cases if case.get('synthetic', False) or 
                          case.get('category') == 'synthetic' or 
                          case.get('id', '').startswith('SYNTHETIC_')]
        real_cases = [case for case in all_cases if not (case.get('synthetic', False) or 
                          case.get('category') == 'synthetic' or 
                          case.get('id', '').startswith('SYNTHETIC_'))]
        
        logger.info(f"   🛡️  V11.9 VIP直通车: {len(synthetic_cases)} 个合成数据绕过清洗器")
        logger.info(f"   🔍 真实数据进入清洗器: {len(real_cases)} 个")
        
        # [V11.7/V11.9] 只对真实数据执行冲突解决（血统论清洗）
        cleaned_real_cases = real_cases
        if CONFLICT_RESOLVER_AVAILABLE and agentic_config.get('use_conflict_resolution', True):
            print("🩸 [V11.9] 执行冲突解决（血统论清洗 - 仅真实数据）...")
            print()
            conflict_resolver = ConflictResolver(config_model=trainer.config_model)
            cleaned_real_cases, removed_ids, removal_notes = conflict_resolver.resolve_all_conflicts(
                real_cases,  # 只清洗真实数据
                similarity_threshold=agentic_config.get('conflict_similarity_threshold', 0.99)  # V11.8: 提升到0.99，几乎完全一样才算冲突
            )
        
        # V11.9: 合并清洗后的真实数据、原有合成数据和黄金数据
        # 黄金数据优先级最高，直接追加（绕过所有清洗）
        all_cases = cleaned_real_cases + synthetic_cases + golden_cases
        
        # V12.0: 重新计算权重和合成标记 - 实施"现实优先"权重策略
        sample_weights = []
        is_synthetic = []
        for case in all_cases:
                is_syn = case.get('synthetic', False)
                category = case.get('category', 'unknown')
                case_id = case.get('id', '')
                is_golden = case.get('golden', False)
                
                # V12.0: 现实优先权重策略
                # Real Data (Classic/Modern): Weight = 10.0
                # Synthetic (Golden): Weight = 1.0
                if is_syn or category == 'synthetic' or case_id.startswith('SYNTHETIC_') or is_golden:
                    # 合成数据（包括Golden）
                    weight = agentic_config.get('synthetic_weight', 1.0)  # V12.0: 默认1.0
                else:
                    # 真实数据（Classic或Modern）
                    if category == 'classic' or case_id.startswith('CLASSIC_'):
                        weight = agentic_config.get('classic_weight', 10.0)  # V12.0: 默认10.0
                    else:
                        weight = agentic_config.get('modern_weight', 10.0)  # V12.0: 默认10.0
                
                sample_weights.append(weight)
                is_synthetic.append(is_syn)
        
        print()
        print(f"   📊 数据集组成（清洗后）:")
        classic_count = sum(1 for i, case in enumerate(all_cases) if not is_synthetic[i] and sample_weights[i] == agentic_config.get('classic_weight', 3.0))
        synthetic_count = sum(is_synthetic)
        modern_count = len(all_cases) - classic_count - synthetic_count
        print(f"      经典案例: {classic_count} 个（权重 {agentic_config.get('classic_weight', 3.0):.1f}）")
        print(f"      合成案例: {synthetic_count} 个（权重 {agentic_config.get('synthetic_weight', 2.0):.1f}）")
        print(f"      现代案例: {modern_count} 个（权重 {agentic_config.get('modern_weight', 1.0):.1f}）")
        if CONFLICT_RESOLVER_AVAILABLE and agentic_config.get('use_conflict_resolution', True) and 'removed_ids' in locals():
            print(f"      删除案例: {len(removed_ids)} 个")
        print()
        
        if len(all_cases) < 20:
            print(f"❌ 数据集太小（{len(all_cases)}个案例），无法训练SVM")
            return
        
        # 提取特征和标签（带合成标记）
        X, y, _ = trainer.extract_features_and_labels(all_cases, mark_synthetic=True)
        sample_weights_array = np.array(sample_weights)
        
        # 训练SVM（V11.1: 使用加权训练、SMOTE和GridSearchCV，严格隔离合成数据）
        # V11.2 Agentic: 从配置读取参数，支持正则化优化
        # V11.9: 调整test_size，确保测试集有足够样本（至少10个）
        test_size = agentic_config.get('test_size', 0.2)
        # 如果真实数据太少，降低test_size以确保测试集至少有10个样本
        real_data_count = sum(1 for syn in is_synthetic if not syn)
        if real_data_count > 0 and real_data_count * test_size < 10:
            test_size = min(0.3, 10.0 / real_data_count)  # 最多30%，确保至少10个测试样本
            logger.info(f"   🔧 调整test_size到 {test_size:.2f}，确保测试集至少有10个样本")
        
        trainer_result = trainer.train_svm(
            X, y, 
            is_synthetic=is_synthetic, 
            test_size=test_size,  # V11.9: 动态调整test_size
            use_smote=agentic_config.get('use_smote', True),  # V11.2: 强制开启
            use_gridsearch=agentic_config.get('use_gridsearch', True),
            sample_weights=sample_weights_array,
            smote_target_ratio=agentic_config.get('smote_target_ratio', 0.4),
            test_random_state=agentic_config.get('test_random_state', 100)  # V11.2: 更换random_state
        )
    
    else:
        # 回退到旧的数据加载方式
        print("⚠️  使用旧的数据加载方式...")
        print()
        
        ignored_ids = trainer.load_ignored_cases()
        real_cases, synthetic_cases = trainer.load_calibration_cases(ignored_ids, include_synthetic=True)
        all_cases = real_cases + synthetic_cases
        
        if len(all_cases) < 20:
            print(f"❌ 数据集太小（{len(all_cases)}个案例），无法训练SVM")
            return
        
        print(f"   📊 数据集组成: 真实 {len(real_cases)} 个, 合成 {len(synthetic_cases)} 个")
        
        X, y, is_synthetic = trainer.extract_features_and_labels(all_cases, mark_synthetic=True)
        
        trainer_result = trainer.train_svm(X, y, is_synthetic=is_synthetic, use_smote=True, use_gridsearch=True)
    
    # 保存模型
    model_file = project_root / "models" / "v11_strength_svm.pkl"
    trainer.save_model(trainer_result, model_file)
    
    print()
    print("=" * 80)
    print("📊 训练结果摘要")
    print("=" * 80)
    print(f"训练集准确率: {trainer_result['train_score']:.2%}", flush=True)
    print(f"测试集准确率: {trainer_result['test_score']:.2%}", flush=True)
    print(f"交叉验证准确率: {trainer_result['cv_mean']:.2%} (±{trainer_result['cv_std']:.2%})", flush=True)
    if trainer_result.get('best_params'):
        print(f"最佳参数: {trainer_result['best_params']}")
        print(f"最佳CV分数: {trainer_result.get('best_cv_score', 0):.2%}")
    print()
    print(f"✅ 模型已保存到: {model_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()

