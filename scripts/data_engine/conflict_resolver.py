"""
V11.7 冲突解决器 (Conflict Resolver)
肃反运动：大清洗与剪枝 (The Great Purge & Pruning)

核心策略：血统论清洗 (Lineage-Based Purge)
既然有冲突，必有一真一假。我们按"血统"决定谁留谁死。

清洗逻辑：
1. 宪法优先：如果 A 是 Classic (古籍)，B 是 Modern (现代)，保留 A，删除 B
2. 理论优先：如果 A 是 Synthetic (理论合成)，B 是 Modern，保留 A，删除 B
3. 内战同归于尽：如果 A 和 B 都是 Modern 且标签矛盾，两个都删除
4. 自身矛盾：如果 A 和 B 是同一个 ID（数据重复）但标签不同，删除该 ID
"""

import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.models.config_model import ConfigModel
from .dynamic_cleaner import DynamicCleaner

logger = logging.getLogger(__name__)


class ConflictResolver:
    """冲突解决器：实施血统论清洗策略"""
    
    def __init__(self, config_model: ConfigModel = None):
        self.config_model = config_model or ConfigModel()
        self.config = self.config_model.load_config()
        self.dynamic_cleaner = DynamicCleaner(config_model=config_model)
        self.ignored_cases_file = project_root / "config" / "ignored_cases.json"
    
    def detect_conflicts(
        self,
        cases: List[Dict],
        similarity_threshold: float = 0.99  # V11.8: 提升到0.99，几乎完全一样才算冲突
    ) -> List[Dict]:
        """
        检测冲突样本对（特征相似但标签不同）
        
        Args:
            cases: 案例列表
            similarity_threshold: 相似度阈值（默认0.95）
        
        Returns:
            冲突样本对列表，每个元素包含：
            - case_a: 案例A的索引和ID
            - case_b: 案例B的索引和ID
            - similarity: 相似度
            - label_a: 案例A的标签
            - label_b: 案例B的标签
        """
        logger.info("🔍 开始检测冲突样本...")
        logger.info(f"   相似度阈值: {similarity_threshold}")
        
        # 提取特征向量
        engine = GraphNetworkEngine(config=self.config)
        features = []
        case_metadata = []
        
        for idx, case in enumerate(cases):
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
                
                feature_vector = engine.extract_svm_features(day_master)
                features.append(feature_vector)
                
                case_metadata.append({
                    'index': idx,
                    'id': case.get('id', f'CASE_{idx}'),
                    'name': case.get('name', 'Unknown'),
                    'label': case.get('ground_truth', {}).get('strength', 'Unknown'),
                    'category': self._get_case_category(case),
                    'case': case
                })
            except Exception as e:
                logger.warning(f"   ⚠️  提取案例 {case.get('id', idx)} 的特征失败: {e}")
                continue
        
        if len(features) < 2:
            logger.warning("   ⚠️  案例数量不足，无法检测冲突")
            return []
        
        X = np.array(features)
        
        # 计算相似度矩阵
        logger.info("   📊 计算特征相似度矩阵...")
        similarity_matrix = cosine_similarity(X)
        
        # 检测冲突对
        conflicts = []
        for i in range(len(X)):
            for j in range(i + 1, len(X)):
                similarity = similarity_matrix[i][j]
                label_i = case_metadata[i]['label']
                label_j = case_metadata[j]['label']
                
                # 如果相似度高但标签不同，则认为是冲突
                if similarity > similarity_threshold and label_i != label_j:
                    conflicts.append({
                        'case_a': {
                            'index': case_metadata[i]['index'],
                            'id': case_metadata[i]['id'],
                            'name': case_metadata[i]['name'],
                            'label': label_i,
                            'category': case_metadata[i]['category']
                        },
                        'case_b': {
                            'index': case_metadata[j]['index'],
                            'id': case_metadata[j]['id'],
                            'name': case_metadata[j]['name'],
                            'label': label_j,
                            'category': case_metadata[j]['category']
                        },
                        'similarity': similarity
                    })
        
        logger.info(f"   ✅ 检测完成，发现 {len(conflicts)} 对冲突样本")
        
        return conflicts
    
    def _get_case_category(self, case: Dict) -> str:
        """
        判断案例的血统类别
        
        Returns:
            'classic', 'synthetic', 或 'modern'
        """
        category = case.get('category', 'unknown')
        case_id = case.get('id', '')
        is_synthetic = case.get('synthetic', False)
        
        if category == 'classic' or case_id.startswith('CLASSIC_'):
            return 'classic'
        elif is_synthetic or category == 'synthetic' or case_id.startswith('SYNTHETIC_'):
            return 'synthetic'
        else:
            return 'modern'
    
    def resolve_conflicts(
        self,
        cases: List[Dict],
        conflicts: List[Dict]
    ) -> Tuple[List[Dict], Set[str], Dict[str, str]]:
        """
        解决冲突：实施血统论清洗策略
        
        清洗逻辑：
        1. 宪法优先：Classic > Modern，保留 Classic，删除 Modern
        2. 理论优先：Synthetic > Modern，保留 Synthetic，删除 Modern
        3. 内战同归于尽：Modern vs Modern，两个都删除
        4. 自身矛盾：同一ID但标签不同，删除该ID
        
        Args:
            cases: 案例列表
            conflicts: 冲突样本对列表
        
        Returns:
            Tuple[cleaned_cases, removed_ids, removal_notes]:
            - cleaned_cases: 清洗后的案例列表
            - removed_ids: 被删除的案例ID集合
            - removal_notes: 删除原因说明
        """
        logger.info("\n" + "=" * 80)
        logger.info("⚔️  [V11.9] 血统论清洗策略 + 外交豁免权 (Lineage-Based Purge + Diplomatic Immunity)")
        logger.info("=" * 80)
        
        # V11.9: 标记受保护的数据（Synthetic数据获得外交豁免权）
        protected_ids = set()
        for case in cases:
            case_id = case.get('id', '')
            category = self._get_case_category(case)
            if category == 'synthetic':
                protected_ids.add(case_id)
        
        logger.info(f"   🛡️  受保护案例数: {len(protected_ids)} (Synthetic数据获得外交豁免权)")
        
        removed_ids = set()
        removal_notes = {}
        
        # 统计各类冲突
        conflict_stats = {
            'classic_vs_modern': 0,
            'synthetic_vs_modern': 0,
            'synthetic_vs_synthetic': 0,
            'modern_vs_modern': 0,
            'self_contradiction': 0,
            'other': 0
        }
        
        for conflict in conflicts:
            case_a = conflict['case_a']
            case_b = conflict['case_b']
            cat_a = case_a['category']
            cat_b = case_b['category']
            id_a = case_a['id']
            id_b = case_b['id']
            
            # 规则1: 自身矛盾（同一ID但标签不同）
            if id_a == id_b:
                removed_ids.add(id_a)
                removal_notes[id_a] = f"自身矛盾：同一ID但标签不同 ({case_a['label']} vs {case_b['label']})"
                conflict_stats['self_contradiction'] += 1
                logger.warning(f"   🚫 自身矛盾: {id_a} - 删除")
                continue
            
            # 规则2: 宪法优先（Classic > Modern）
            if cat_a == 'classic' and cat_b == 'modern':
                removed_ids.add(id_b)
                removal_notes[id_b] = f"血统论清洗：Classic ({id_a}) vs Modern ({id_b})，保留Classic，删除Modern"
                conflict_stats['classic_vs_modern'] += 1
                logger.info(f"   ⚔️  宪法优先: 保留 {id_a} (Classic), 删除 {id_b} (Modern)")
                continue
            
            if cat_a == 'modern' and cat_b == 'classic':
                removed_ids.add(id_a)
                removal_notes[id_a] = f"血统论清洗：Modern ({id_a}) vs Classic ({id_b})，保留Classic，删除Modern"
                conflict_stats['classic_vs_modern'] += 1
                logger.info(f"   ⚔️  宪法优先: 保留 {id_b} (Classic), 删除 {id_a} (Modern)")
                continue
            
            # 规则3: 理论优先（Synthetic > Modern）- V12.0: 保留Synthetic，但Modern标记为conflicted后保留
            if cat_a == 'synthetic' and cat_b == 'modern':
                # V12.0: Synthetic依然受保护，但Modern不再删除，而是标记为conflicted后保留
                case_obj_b = case_b.get('case', {})
                if 'conflicted' not in case_obj_b:
                    case_obj_b['conflicted'] = []
                case_obj_b['conflicted'].append({
                    'conflict_id': id_a,
                    'conflict_label': case_a['label'],
                    'similarity': conflict.get('similarity', 0.0),
                    'reason': 'Synthetic基准冲突'
                })
                conflict_stats['synthetic_vs_modern'] += 1
                logger.info(f"   🛡️  V12.0保留策略: Synthetic ({id_a}) vs Modern ({id_b})，保留两者，Modern标记为conflicted")
                continue
            
            if cat_a == 'modern' and cat_b == 'synthetic':
                # V12.0: Synthetic依然受保护，但Modern不再删除，而是标记为conflicted后保留
                case_obj_a = case_a.get('case', {})
                if 'conflicted' not in case_obj_a:
                    case_obj_a['conflicted'] = []
                case_obj_a['conflicted'].append({
                    'conflict_id': id_b,
                    'conflict_label': case_b['label'],
                    'similarity': conflict.get('similarity', 0.0),
                    'reason': 'Synthetic基准冲突'
                })
                conflict_stats['synthetic_vs_modern'] += 1
                logger.info(f"   🛡️  V12.0保留策略: Modern ({id_a}) vs Synthetic ({id_b})，保留两者，Modern标记为conflicted")
                continue
            
            # V11.9: Synthetic vs Classic - 尊重古籍，但Synthetic仍受保护
            if cat_a == 'synthetic' and cat_b == 'classic':
                # Classic优先级更高，但Synthetic不会被Modern删除
                if id_a not in protected_ids or id_b in protected_ids:  # 如果B也是protected（不应该发生），则保留Classic
                    removed_ids.add(id_a)
                    removal_notes[id_a] = f"血统论清洗：Synthetic ({id_a}) vs Classic ({id_b})，保留Classic（古籍优先），删除Synthetic"
                    conflict_stats['other'] += 1
                    logger.info(f"   ⚔️  古籍优先: 保留 {id_b} (Classic), 删除 {id_a} (Synthetic)")
                continue
            
            if cat_a == 'classic' and cat_b == 'synthetic':
                # Classic优先级更高
                if id_b not in protected_ids or id_a in protected_ids:  # 如果A也是protected（不应该发生），则保留Classic
                    removed_ids.add(id_b)
                    removal_notes[id_b] = f"血统论清洗：Classic ({id_a}) vs Synthetic ({id_b})，保留Classic（古籍优先），删除Synthetic"
                    conflict_stats['other'] += 1
                    logger.info(f"   ⚔️  古籍优先: 保留 {id_a} (Classic), 删除 {id_b} (Synthetic)")
                continue
            
            # V11.9: Synthetic vs Synthetic - 处理重复和冲突
            if cat_a == 'synthetic' and cat_b == 'synthetic':
                label_a = case_a['label']
                label_b = case_b['label']
                
                if label_a == label_b:
                    # 标签相同：视为重复，保留其中一个（保留ID较小的）
                    removed_id = id_a if id_a > id_b else id_b
                    if removed_id not in protected_ids:  # 双重保险
                        removed_ids.add(removed_id)
                        removal_notes[removed_id] = f"血统论清洗：Synthetic重复（标签相同），保留 {id_a if removed_id == id_b else id_b}，删除 {removed_id}"
                        conflict_stats['synthetic_vs_synthetic'] += 1
                        logger.debug(f"   🔄 Synthetic重复: 保留 {id_a if removed_id == id_b else id_b}, 删除 {removed_id}")
                else:
                    # 标签不同：罕见情况，删除两个（但实际不应该发生，因为合成数据是理论基准）
                    if id_a not in protected_ids and id_b not in protected_ids:
                        removed_ids.add(id_a)
                        removed_ids.add(id_b)
                        removal_notes[id_a] = f"血统论清洗：Synthetic内战（标签不同），删除 {id_a}"
                        removal_notes[id_b] = f"血统论清洗：Synthetic内战（标签不同），删除 {id_b}"
                        conflict_stats['synthetic_vs_synthetic'] += 1
                        logger.warning(f"   ⚠️  Synthetic内战（标签不同）: 删除两个 ({id_a} vs {id_b})")
                continue
            
            # 规则4: Modern内战 - V12.0: 停止内卷，全部保留
            if cat_a == 'modern' and cat_b == 'modern':
                similarity = conflict.get('similarity', 0.0)
                label_a = case_a['label']
                label_b = case_b['label']
                
                # V12.0: 废除删除逻辑，全部保留
                # Random Forest擅长处理噪声，可以同时接受两个冲突点并算出概率
                # 标记为conflicted但保留在数据集中
                case_obj_a = case_a.get('case', {})
                case_obj_b = case_b.get('case', {})
                
                # 标记冲突但保留
                if 'conflicted' not in case_obj_a:
                    case_obj_a['conflicted'] = []
                case_obj_a['conflicted'].append({
                    'conflict_id': id_b,
                    'conflict_label': label_b,
                    'similarity': similarity
                })
                
                if 'conflicted' not in case_obj_b:
                    case_obj_b['conflicted'] = []
                case_obj_b['conflicted'].append({
                    'conflict_id': id_a,
                    'conflict_label': label_a,
                    'similarity': similarity
                })
                
                conflict_stats['modern_vs_modern'] += 1
                logger.info(f"   ✅ V12.0停止内卷: Modern内战 ({id_a} vs {id_b})，全部保留 (相似度{similarity:.3f}, 标签{label_a} vs {label_b})")
                continue
            
            # V11.9: 其他情况已在上面处理（Synthetic vs Classic, Synthetic vs Synthetic等）
            # 如果还有未处理的情况，记录警告
            logger.debug(f"   ⚠️  未处理的冲突类型: {cat_a} vs {cat_b} ({id_a} vs {id_b})")
        
        # 过滤掉被删除的案例
        cleaned_cases = [
            case for case in cases
            if case.get('id', '') not in removed_ids
        ]
        
        # 打印统计信息
        logger.info("\n📊 清洗统计:")
        logger.info(f"   原始案例数: {len(cases)}")
        logger.info(f"   冲突对数: {len(conflicts)}")
        logger.info(f"   删除案例数: {len(removed_ids)}")
        logger.info(f"   清洗后案例数: {len(cleaned_cases)}")
        logger.info(f"\n📈 冲突类型分布:")
        logger.info(f"   Classic vs Modern: {conflict_stats['classic_vs_modern']} 对")
        logger.info(f"   Synthetic vs Modern: {conflict_stats['synthetic_vs_modern']} 对")
        logger.info(f"   Synthetic vs Synthetic: {conflict_stats['synthetic_vs_synthetic']} 对")
        logger.info(f"   Modern vs Modern (内战): {conflict_stats['modern_vs_modern']} 对")
        logger.info(f"   自身矛盾: {conflict_stats['self_contradiction']} 个")
        logger.info(f"   其他: {conflict_stats['other']} 对")
        logger.info("=" * 80 + "\n")
        
        return cleaned_cases, removed_ids, removal_notes
    
    def save_removed_cases(self, removed_ids: Set[str], removal_notes: Dict[str, str]):
        """
        将被删除的案例ID追加到 ignored_cases.json
        
        Args:
            removed_ids: 被删除的案例ID集合
            removal_notes: 删除原因说明
        """
        # 加载现有的忽略列表
        existing_ignored = self.dynamic_cleaner.load_ignored_cases()
        
        # 合并新的删除列表
        all_ignored = existing_ignored | removed_ids
        
        # 更新notes
        existing_notes = {}
        if self.ignored_cases_file.exists():
            with open(self.ignored_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_notes = data.get('notes', {})
        
        # 合并notes
        all_notes = {**existing_notes, **removal_notes}
        
        # 保存
        self.dynamic_cleaner.save_ignored_cases(all_ignored, all_notes)
        
        logger.info(f"✅ 已将 {len(removed_ids)} 个冲突案例追加到 ignored_cases.json")
        logger.info(f"   总忽略案例数: {len(all_ignored)}")
    
    def resolve_all_conflicts(
        self,
        cases: List[Dict],
        similarity_threshold: float = 0.95
    ) -> Tuple[List[Dict], Set[str], Dict[str, str]]:
        """
        完整的冲突解决流程：检测 + 解决 + 保存
        
        Args:
            cases: 案例列表
            similarity_threshold: 相似度阈值
        
        Returns:
            Tuple[cleaned_cases, removed_ids, removal_notes]
        """
        logger.info("\n" + "=" * 80)
        logger.info("🩸 [V11.7] 肃反运动：大清洗与剪枝")
        logger.info("=" * 80)
        logger.info("执行血统论清洗策略，消灭矛盾数据...\n")
        
        # 1. 检测冲突
        conflicts = self.detect_conflicts(cases, similarity_threshold)
        
        if not conflicts:
            logger.info("✅ 未发现冲突样本，数据已干净")
            return cases, set(), {}
        
        # 2. 解决冲突
        cleaned_cases, removed_ids, removal_notes = self.resolve_conflicts(cases, conflicts)
        
        # 3. 保存删除列表
        if removed_ids:
            self.save_removed_cases(removed_ids, removal_notes)
        
        return cleaned_cases, removed_ids, removal_notes


if __name__ == '__main__':
    """测试冲突解决器"""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    from .data_loader import DataLoader
    
    # 加载数据
    loader = DataLoader()
    cases, weights, is_synthetic = loader.load_training_cases(
        use_dynamic_cleaning=False,  # 先不动态清洗，让冲突解决器处理
        generate_synthetic=True,
        synthetic_count=30
    )
    
    logger.info(f"\n📦 加载了 {len(cases)} 个案例")
    
    # 创建冲突解决器
    resolver = ConflictResolver()
    
    # 执行冲突解决
    cleaned_cases, removed_ids, removal_notes = resolver.resolve_all_conflicts(
        cases,
        similarity_threshold=0.95
    )
    
    logger.info(f"\n✅ 冲突解决完成")
    logger.info(f"   原始案例: {len(cases)} 个")
    logger.info(f"   清洗后案例: {len(cleaned_cases)} 个")
    logger.info(f"   删除案例: {len(removed_ids)} 个")
    
    if removed_ids:
        logger.info(f"\n   删除的案例ID:")
        for case_id in sorted(removed_ids):
            logger.info(f"      - {case_id}: {removal_notes.get(case_id, 'N/A')}")

