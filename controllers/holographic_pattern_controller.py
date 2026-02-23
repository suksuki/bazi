"""
全息格局控制器 (Holographic Pattern Controller)
MVC Controller Layer - 负责全息格局的业务逻辑

严格遵循MVC架构原则：
- View层（holographic_pattern.py）只负责UI展示和用户交互
- Controller层封装所有算法逻辑，协调Engine和Model
- Engine层负责核心计算

注意：这是全新的"张量全息格局"系统，不依赖现有的物理模型仿真注册表
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.engine_graph.constants import TWELVE_LIFE_STAGES
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine

logger = logging.getLogger(__name__)


class HolographicPatternController:
    """
    全息格局控制器
    
    职责：
    - 封装全息格局相关的业务逻辑
    - 协调格局注册表的加载和查询（使用新的"张量全息格局"注册表）
    - 处理五维张量投影计算
    - 提供统一的数据接口给View层
    """
    
    def __init__(self):
        """初始化控制器"""
        # 使用新的"张量全息格局"注册表路径
        self.registry_path = Path(__file__).parent.parent / "core" / "subjects" / "holographic_pattern" / "registry.json"
        self.registry = None
        self.framework = QuantumUniversalFramework()
        # 初始化RegistryLoader用于V2.1+版本的计算
        from core.registry_loader import RegistryLoader
        self.registry_loader = RegistryLoader()
        logger.info("HolographicPatternController initialized (全新张量全息格局系统)")
    
    def load_registry(self) -> Dict:
        """
        加载格局注册表
        
        Returns:
            注册表字典
        """
        if self.registry is None:
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
                logger.info(f"✅ 已加载注册表: {len(self.registry.get('patterns', {}))} 个格局")
            except Exception as e:
                logger.error(f"加载注册表失败: {e}")
                self.registry = {"patterns": {}, "metadata": {}}
        
        return self.registry
    
    def _get_display_name_cn(self, pattern_data: Dict, pattern_id: str) -> str:
        """Helper to extract display name in Chinese."""
        if pattern_data.get('name_cn'):
            return pattern_data['name_cn']
        
        # Try meta_info Chinese Name (Primary source after normalization)
        if 'meta_info' in pattern_data and pattern_data['meta_info'].get('chinese_name'):
            return pattern_data['meta_info']['chinese_name']
            
        # Try meta_info Display Name but mark as English
        if 'meta_info' in pattern_data and pattern_data['meta_info'].get('name'):
            return pattern_data['meta_info']['name']
            
        # Try Regex from name if format is 'Name (ChineseName)'
        name = pattern_data.get('name', '')
        if '(' in name and ')' in name:
            import re
            match = re.search(r'[\(（](.*?)[\)）]', name)
            if match:
                return match.group(1)
                
        return name if name else pattern_id

    def get_all_patterns(self) -> List[Dict]:
        """
        获取所有格局列表（按QGA-HR V1.0层级命名规范）
        支持主格局和子格局的层级关系
        
        Returns:
            格局列表，按Category和Subject ID排序，子格局跟随主格局
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        # 分离主格局和子格局
        main_patterns = []
        sub_patterns = []
        
        for pattern_id, pattern_data in patterns.items():
            # 提取层级信息
            category = pattern_data.get('category', '')
            subject_id = pattern_data.get('subject_id', pattern_id)
            parent_pattern = pattern_data.get('parent_pattern')
            
            p_info = {
                'id': pattern_id,
                'category': category,
                'subject_id': subject_id,
                'name': pattern_data.get('name', pattern_id),
                'name_cn': self._get_display_name_cn(pattern_data, pattern_id),
                'icon': pattern_data.get('icon', '🧬'),
                'description': pattern_data.get('description', ''),
                'version': pattern_data.get('version', 'N/A'),
                'active': pattern_data.get('active', True),
                'parent_pattern': parent_pattern,
                'is_sub_pattern': parent_pattern is not None
            }
            
            if parent_pattern:
                sub_patterns.append(p_info)
            else:
                main_patterns.append(p_info)
                # [V2.5] 发现嵌套子格局
                # [V2.5] 发现嵌套子格局 (支持 sub_patterns_registry 和 sub_patterns)
                sub_patterns_data = pattern_data.get('sub_patterns_registry') or pattern_data.get('sub_patterns') or []
                if sub_patterns_data:
                    for sub_data in sub_patterns_data:
                        sub_info = {
                            'id': sub_data.get('id'),
                            'category': category,
                            'subject_id': sub_data.get('subject_id', sub_data.get('id')),
                            'name': sub_data.get('name'),
                            'name_cn': self._get_display_name_cn(sub_data, sub_data.get('id')),
                            'icon': sub_data.get('icon', p_info['icon']),
                            'description': sub_data.get('description'),
                            'version': p_info['version'],
                            'active': True,
                            'parent_pattern': pattern_id,
                            'is_sub_pattern': True
                        }
                        sub_patterns.append(sub_info)
        
        # 主格局按Category和Subject ID排序
        main_patterns.sort(key=lambda x: (x.get('category', ''), x.get('subject_id', '')))
        
        # 子格局按父格局分组，然后按Subject ID排序
        sub_patterns_by_parent = {}
        for sub_pattern in sub_patterns:
            parent_id = sub_pattern['parent_pattern']
            if parent_id not in sub_patterns_by_parent:
                sub_patterns_by_parent[parent_id] = []
            sub_patterns_by_parent[parent_id].append(sub_pattern)
        
        # 对每个父格局的子格局排序
        for parent_id in sub_patterns_by_parent:
            sub_patterns_by_parent[parent_id].sort(key=lambda x: x.get('subject_id', ''))
        
        # 构建层级结果：主格局 + 其子格局
        result = []
        for main_pattern in main_patterns:
            # 添加主格局
            result.append(main_pattern)
            
            # 添加该主格局的子格局
            main_id = main_pattern['id']
            if main_id in sub_patterns_by_parent:
                for sub_pattern in sub_patterns_by_parent[main_id]:
                    result.append(sub_pattern)
        
        # 处理没有父格局的子格局（理论上不应该有，但为了健壮性）
        for sub_pattern in sub_patterns:
            if sub_pattern['parent_pattern'] not in [p['id'] for p in main_patterns]:
                result.append(sub_pattern)
        
        return result

    def get_fds_sop_patterns(self) -> List[Dict[str, Any]]:
        """
        从 FDS SOP 法定路径 registry/holographic_pattern/ 发现所有格局及其审计状态。
        用于全息格局页「格局审计看板」展示（FDS SOP V4.0）。
        
        Returns:
            [{"pattern_id", "name_cn", "version", "status": "已审计"|"在审计", "source": "manifest"|"registry", "path"}]
        """
        project_root = Path(__file__).parent.parent
        reg_dir = project_root / "registry" / "holographic_pattern"
        out = []
        if not reg_dir.exists():
            return out
        # 1) 根目录 *.json（如 A-01.json）
        for j in sorted(reg_dir.glob("*.json")):
            if j.name.startswith("_"):
                continue
            try:
                with open(j, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            pid = data.get("pattern_id") or data.get("id") or j.stem
            meta = data.get("meta_info") or {}
            name_cn = meta.get("chinese_name") or meta.get("display_name") or pid
            ver = data.get("version", "N/A")
            # A-01 已审计；A-02 及其余为在审计中（显式约定）
            if pid == "A-01":
                status = "已审计"
            else:
                status = "在审计中"
            out.append({
                "pattern_id": pid,
                "name_cn": name_cn,
                "version": str(ver),
                "status": status,
                "source": "registry",
                "path": str(j),
            })
        # 2) 子目录 */A-*_manifest.json（如 A-02/A-02_manifest.json）
        for sub in sorted(reg_dir.iterdir()):
            if not sub.is_dir():
                continue
            manifest = sub / f"{sub.name}_manifest.json"
            if not manifest.exists():
                manifest = next(sub.glob("*_manifest.json"), None)
            if not manifest:
                continue
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            pid = data.get("pattern_id") or sub.name
            meta = data.get("meta_info") or {}
            name_cn = meta.get("chinese_name") or meta.get("display_name") or pid
            ver = data.get("version", "N/A")
            # A-01 已审计；A-02 在审计中（显式约定）
            status = "已审计" if pid == "A-01" else "在审计中"
            out.append({
                "pattern_id": pid,
                "name_cn": name_cn,
                "version": str(ver),
                "status": status,
                "source": "manifest",
                "path": str(manifest),
            })
        # 3) 若 registry 中无 A-01，从 config/patterns/manifest_A01.json 补充，保证页面上可选 A-01
        if not any(x["pattern_id"] == "A-01" for x in out):
            manifest_a01 = project_root / "config" / "patterns" / "manifest_A01.json"
            if manifest_a01.exists():
                try:
                    with open(manifest_a01, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    meta = data.get("meta_info") or {}
                    out.append({
                        "pattern_id": "A-01",
                        "name_cn": meta.get("chinese_name") or meta.get("display_name") or "正官格",
                        "version": str(data.get("version", "N/A")),
                        "status": "已审计",
                        "source": "manifest",
                        "path": str(manifest_a01),
                    })
                except Exception:
                    pass
        out.sort(key=lambda x: (x["pattern_id"], x["source"]))
        return out

    def get_fds_pattern_detail(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 FDS 格局完整详情（用于已审计格局的详情展示与 LLM 解读）。
        来源：registry/holographic_pattern/ 或 config/patterns/manifest_A01.json（A-01）。
        """
        project_root = Path(__file__).parent.parent
        reg_dir = project_root / "registry" / "holographic_pattern"
        pid = (pattern_id or "").strip().upper()
        data = None
        if pid == "A-01":
            for path in [reg_dir / "A-01.json", project_root / "config" / "patterns" / "manifest_A01.json"]:
                if path.exists():
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        break
                    except Exception:
                        continue
        else:
            sub_dir = reg_dir / pid
            manifest = sub_dir / f"{pid}_manifest.json" if sub_dir.exists() else None
            if manifest and manifest.exists():
                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass
        if not data:
            return None
        meta = data.get("meta_info") or {}
        rules = data.get("classical_logic_rules") or {}
        subs = data.get("sub_pattern_definitions") or {}
        semantic = data.get("semantic_core_dimensions") or {}
        if not semantic and pid == "A-01":
            try:
                hkb_path = project_root / "config" / "hkb" / "hkb_params.json"
                if hkb_path.exists():
                    with open(hkb_path, "r", encoding="utf-8") as f:
                        hkb = json.load(f)
                    core = (hkb.get("hkb") or {}).get("a01_semantic_core") or {}
                    semantic = {k: {"name": v.get("name", k), "definition": v.get("definition"), "physical_mapping": v.get("physical_mapping"), "classical_by_gemini": (v.get("definition") or "") + " " + (v.get("physical_mapping") or "")} for k, v in core.items() if isinstance(v, dict)}
            except Exception:
                pass
        tmm = data.get("tensor_mapping_matrix") or {}
        strong = tmm.get("strong_correlation") or []
        sub_list = [{"id": k, "name": v.get("name", k)} for k, v in subs.items()]
        return {
            "pattern_id": data.get("pattern_id") or pid,
            "version": data.get("version", "N/A"),
            "meta_info": meta,
            "classical_logic_rules": {"description": rules.get("description", ""), "expression": rules.get("expression")},
            "sub_pattern_definitions": sub_list,
            "semantic_core_dimensions": semantic,
            "strong_correlation": strong,
            "centroids": data.get("centroids"),
            "benchmarks": data.get("benchmarks"),
        }

    def get_pattern_hierarchy(self) -> Dict[str, Dict]:
        """
        获取格局层级结构（主格局 -> 子格局）
        
        Returns:
            字典：{主格局ID: {'main': 主格局信息, 'subs': [子格局列表]}}
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        hierarchy = {}
        
        # 先找出所有主格局
        for pattern_id, pattern_data in patterns.items():
            parent_pattern = pattern_data.get('parent_pattern')
            if not parent_pattern:  # 主格局
                category = pattern_data.get('category', '')
                subject_id = pattern_data.get('subject_id', pattern_id)
                
                hierarchy[pattern_id] = {
                    'main': {
                        'id': pattern_id,
                        'category': category,
                        'subject_id': subject_id,
                        'name': pattern_data.get('name', pattern_id),
                        'name_cn': self._get_display_name_cn(pattern_data, pattern_id),
                        'icon': pattern_data.get('icon', '🧬'),
                        'description': pattern_data.get('description', ''),
                        'version': pattern_data.get('version', 'N/A'),
                        'active': pattern_data.get('active', False)
                    },
                    'subs': []
                }
        
        # 再找出所有子格局并归类
        for pattern_id, pattern_data in patterns.items():
            parent_pattern = pattern_data.get('parent_pattern')
            if parent_pattern and parent_pattern in hierarchy:
                # ... (existing flat logic)
                pass # Already handled by flat structure
            
            # [V2.5] 发现嵌套子格局 (支持 sub_patterns_registry 和 sub_patterns)
            sub_patterns_list = pattern_data.get('sub_patterns_registry') or pattern_data.get('sub_patterns') or []
            if sub_patterns_list and pattern_id in hierarchy:
                for sub_data in sub_patterns_list:
                    # 使用 helper 获取中文名
                    name_cn = self._get_display_name_cn(sub_data, sub_data.get('id'))
                            
                    hierarchy[pattern_id]['subs'].append({
                        'id': sub_data.get('id'),
                        'category': hierarchy[pattern_id]['main']['category'],
                        'subject_id': sub_data.get('subject_id', sub_data.get('id')),
                        'name': sub_data.get('name'),
                        'name_cn': name_cn,
                        'icon': sub_data.get('icon', hierarchy[pattern_id]['main']['icon']), # Inherit icon if missing
                        'description': sub_data.get('description'),
                        'version': hierarchy[pattern_id]['main']['version'],
                        'active': True
                    })
        
        # 对每个主格局的子格局排序
        for parent_id in hierarchy:
            hierarchy[parent_id]['subs'].sort(key=lambda x: x.get('subject_id', ''))
        
        return hierarchy
    
    def calculate_evolution(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        year: int,
        geo_city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        计算动态演化状态（基于FDS-V1.1 Step 6）
        
        Args:
            pattern_id: 格局ID
            chart: 四柱八字
            day_master: 日主
            year: 演化年份
            geo_city: 地理城市（可选）
            
        Returns:
            演化结果字典，包含：
            - base_tensor: 原局基态张量
            - luck_tensor: 大运注入后的张量
            - year_tensor: 流年注入后的张量
            - final_tensor: 地理修正后的最终张量
            - status: 输出状态（STABLE, CRITICAL, FRACTURED, MUTATED）
            - deformation_type: 形变类型（ELASTIC, PLASTIC, FRACTURE）
        """
        try:
            # 1. 计算原局基态
            base_result = self.calculate_tensor_projection(pattern_id, chart, day_master)
            if 'error' in base_result:
                return {'error': base_result['error']}
            
            base_tensor = base_result['projection']
            
            # 2. 获取大运和流年（简化：使用框架计算）
            # 这里需要从BaziProfile获取，暂时简化处理
            from core.bazi_profile import BaziProfile
            from datetime import datetime
            
            # 创建临时BaziProfile用于计算大运流年
            # 注意：这里需要完整的出生信息，暂时使用简化方法
            # Controller不应该直接访问session_state，应该通过参数传入
            luck_pillar = "甲子"  # 默认值，实际应该从context传入
            year_pillar = "甲子"  # 默认值，实际应该从context传入
            
            # 3. 计算大运注入（简化：使用固定系数）
            luck_tensor = base_tensor.copy()
            # 这里应该根据大运干支计算影响，暂时简化
            luck_effect = 1.0  # 默认无影响
            
            # 4. 计算流年注入（主要影响S轴）
            year_tensor = luck_tensor.copy()
            # 简化：流年主要影响应力轴
            year_impulse = 0.0  # 默认无脉冲
            
            # 5. 地理修正（如果有）
            final_tensor = year_tensor.copy()
            if geo_city:
                from ui.pages.quantum_lab import GEO_CITY_MAP
                if geo_city in GEO_CITY_MAP:
                    geo_factor, geo_element = GEO_CITY_MAP[geo_city]
                    # 根据五行偏向修正对应轴
                    element_axis_map = {
                        'Fire': 'E',
                        'Earth': 'M',
                        'Metal': 'O',
                        'Water': 'R',
                        'Wood': 'S'
                    }
                    target_axis = element_axis_map.get(geo_element, 'E')
                    final_tensor[target_axis] = final_tensor.get(target_axis, 0) * geo_factor
            
            # 6. 获取断裂阈值（从注册表）
            pattern = self.get_pattern_by_id(pattern_id)
            fracture_threshold = 50.0  # 默认值
            if pattern:
                dynamic_sim = pattern.get('kinetic_evolution', {}).get('dynamic_simulation', {})
                fracture_threshold = dynamic_sim.get('fracture_threshold', 50.0)
            
            # 7. 判定输出状态
            # 注意：final_tensor的值是投影值（已经乘以SAI），需要转换为应力百分比
            # 简化处理：使用S轴的投影值作为应力指标
            s_projection = final_tensor.get('S', 0)
            # 将投影值转换为应力百分比（假设SAI=1.0时，S投影值=权重，需要放大）
            # 这里简化：直接使用S投影值，如果SAI>0则用SAI归一化
            base_sai = base_result.get('sai', 1.0)
            if base_sai > 0:
                s_value = (s_projection / base_sai) * 100  # 转换为百分比
            else:
                s_value = s_projection * 100  # 如果SAI为0，直接使用投影值
            
            if s_value < 0.6 * fracture_threshold:
                status = 'STABLE'
                deformation_type = 'ELASTIC'
            elif s_value < fracture_threshold:
                status = 'CRITICAL'
                deformation_type = 'PLASTIC'
            else:
                status = 'FRACTURED'
                deformation_type = 'FRACTURE'
            
            # 8. 生成描述
            description = f"在{year}年，系统处于{status}状态"
            if geo_city:
                description += f"，地理环境：{geo_city}"
            
            return {
                'base_tensor': base_tensor,
                'luck_tensor': luck_tensor,
                'year_tensor': year_tensor,
                'final_tensor': final_tensor,
                'status': status,
                'deformation_type': deformation_type,
                'description': description,
                'year': year,
                'geo_city': geo_city
            }
            
        except Exception as e:
            logger.error(f"计算动态演化失败: {e}", exc_info=True)
            return {'error': str(e)}
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict]:
        """
        根据ID获取格局详情
        支持在主格局和嵌套子格局中查找
        """
        registry = self.load_registry()
        patterns = registry.get('patterns', {})
        
        # 1. 检查主格局
        if pattern_id in patterns:
            return patterns[pattern_id]
        
        # 2. 检查嵌套子格局
        for pid, data in patterns.items():
            if 'sub_patterns_registry' in data:
                for sub in data['sub_patterns_registry']:
                    if sub.get('id') == pattern_id:
                        # [V2.5] 自动合并主格局的内核配置以支持计算
                        combined = sub.copy()
                        combined['physics_kernel'] = sub.get('physics_kernel', data.get('physics_kernel'))
                        combined['version'] = sub.get('version', data.get('version', '2.5'))
                        return combined
        
        return None
    
    def _chart_to_ten_gods(self, chart: List[str], day_master: str) -> Dict[str, float]:
        """从四柱与日主计算十神能量向量（与 FDS/pattern_engine 一致），返回 ZG, PG, ..."""
        from core.physics_engine import compute_energy_flux
        en_to_code = {
            "bi_jian": "ZB", "jie_cai": "PB", "shi_shen": "ZS", "shang_guan": "PS",
            "zheng_cai": "ZR", "pian_cai": "PR", "zheng_guan": "ZG", "qi_sha": "PG",
            "zheng_yin": "ZC", "pian_yin": "PC",
        }
        en_to_cn = {
            "bi_jian": "比肩", "jie_cai": "劫财", "shi_shen": "食神", "shang_guan": "伤官",
            "zheng_cai": "正财", "pian_cai": "偏财", "zheng_guan": "正官", "qi_sha": "七杀",
            "zheng_yin": "正印", "pian_yin": "偏印",
        }
        out = {}
        for en, code in en_to_code.items():
            cn = en_to_cn.get(en, "")
            if cn:
                try:
                    out[code] = float(compute_energy_flux(chart, day_master, cn))
                except Exception:
                    out[code] = 0.0
        return out

    def _calculate_fds_projection(self, pattern_id: str, chart: List[str], day_master: str, context: Optional[Dict]) -> Optional[Dict]:
        """A-01/A-02 专用：用 FDS 推理或 TMM 投影，返回与 calculate_tensor_projection 一致的结构。"""
        project_root = Path(__file__).parent.parent
        ten_gods = self._chart_to_ten_gods(chart, day_master)
        registry_path = project_root / "registry" / "holographic_pattern" / f"{pattern_id}.json"
        manifest_path = project_root / "config" / "patterns" / "manifest_A01.json"
        if pattern_id == "A-02":
            manifest_path = project_root / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
        if registry_path.exists() and manifest_path.exists():
            try:
                from core.fds_inference_engine import FDSInferenceEngine
                engine = FDSInferenceEngine(registry_path=registry_path, manifest_path=manifest_path)
                inf = engine.infer(ten_gods, extra_context={"self_energy": {"E": 0.5}})
                point = inf.get("point") or {}
                best = inf.get("best_subpattern", "")
                dists = inf.get("distances") or {}
                return {
                    "projection": point,
                    "sai": float(inf.get("similarity_score") or (inf.get("similarity_percent", 0) / 100.0) or 0.5),
                    "recognition": {
                        "mahalanobis_dist": list(dists.values())[0] if dists else 0,
                        "precision_score": (inf.get("similarity_percent") or 0) / 100.0,
                        "pattern_type": "STANDARD" if best else "UNKNOWN",
                        "description": (inf.get("knowledge") or {}).get("description", "流形归位"),
                    },
                    "sub_id": best,
                    "pattern_name": "正官格" if pattern_id == "A-01" else "七杀格",
                }
            except Exception as e:
                logger.warning("FDS 推理失败，回退 TMM 投影: %s", e)
        try:
            import numpy as np
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tmm = (data.get("tensor_mapping_matrix") or {}).get("weights")
            if not tmm:
                from core.tensor_mapping_loader import load_tensor_mapping_matrix
                tmm_dict, _ = load_tensor_mapping_matrix(data, None)
                tmm = tmm_dict.get("weights", {})
                order = tmm_dict.get("ten_gods", [])
                dims = tmm_dict.get("dimensions", ["E", "O", "M", "S", "R"])
            else:
                order = (data.get("tensor_mapping_matrix") or {}).get("ten_gods", [])
                dims = (data.get("tensor_mapping_matrix") or {}).get("dimensions", ["E", "O", "M", "S", "R"])
            if not tmm or not order:
                return None
            weights = np.array([tmm[g] for g in order])
            vec = np.array([float(ten_gods.get(g, 0)) for g in order])
            point_5d = np.dot(weights.T, vec)
            point = {d: float(point_5d[i]) for i, d in enumerate(dims)}
            return {
                "projection": point,
                "sai": 0.5,
                "recognition": {"mahalanobis_dist": 0, "precision_score": 0.5, "pattern_type": "STANDARD", "description": "基于 TMM 投影（无质心）"},
                "sub_id": None,
                "pattern_name": "正官格" if pattern_id == "A-01" else "七杀格",
            }
        except Exception as e:
            logger.exception("TMM 投影回退失败: %s", e)
        return None

    def calculate_tensor_projection(self, pattern_id: str, chart: List[str], 
                                   day_master: str, context: Optional[Dict] = None) -> Dict:
        """
        计算五维张量投影（支持FDS-V3.0及历史版本V1.5+/V2.1+）
        
        Args:
            pattern_id: 格局ID
            chart: 八字原局
            day_master: 日主
            context: 上下文（大运、流年等）
            
        Returns:
            五维张量投影结果
        """
        pid = (pattern_id or "").strip().upper()
        if pid in ("A-01", "A-02"):
            fds_result = self._calculate_fds_projection(pid, chart, day_master, context)
            if fds_result:
                return fds_result
        # 获取格局信息（旧 registry）
        pattern = self.get_pattern_by_id(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        # [V3.0 Update] Detect Matrix Protocol by kernel signature or version string
        version = str(pattern.get('version', '1.0'))
        physics_kernel = pattern.get('physics_kernel', {})
        is_matrix_protocol = (
            str(version) >= '1.5' or 
            str(version).startswith('3.') or
            physics_kernel.get('transfer_matrix') is not None
        )
        
        logger.debug(f"格局 {pattern_id} 核验: version={version!r}, is_matrix_protocol={is_matrix_protocol}")
        
        # V1.5+/V2.1+/V3.0+: 使用RegistryLoader的矩阵投影方法
        if is_matrix_protocol:
            logger.info(f"✅ 检测到矩阵协议格局 {pattern_id}，使用transfer_matrix计算")
            try:
                if not hasattr(self, 'registry_loader') or self.registry_loader is None:
                    logger.error("RegistryLoader未初始化！")
                    return {'error': 'RegistryLoader未初始化，无法使用V3.0矩阵计算'}
                
                result = self.registry_loader.calculate_tensor_projection_from_registry(
                    pattern_id=pattern_id,
                    chart=chart,
                    day_master=day_master,
                    context=context
                )
                
                logger.info(f"V3.0计算结果: sai={result.get('sai', 'N/A')}, projection={result.get('projection', {})}")
                
                # 检查是否有错误
                if 'error' in result:
                    logger.error(f"V3.0计算返回错误: {result['error']}")
                    return result
                
                # 检查SAI是否为0
                if result.get('sai', 0) == 0:
                    logger.warning(f"⚠️ V3.0计算返回SAI=0，检查计算逻辑")
                    # 检查是否有raw_projection
                    raw_projection = result.get('raw_projection', {})
                    if raw_projection:
                        logger.warning(f"raw_projection: {raw_projection}")
                    # 检查frequency_vector
                    frequency_vector = result.get('frequency_vector', {})
                    if frequency_vector:
                        logger.warning(f"frequency_vector: {frequency_vector}")
                
                # 确保返回格式与旧版本兼容
                # 添加pattern_name等字段以保持兼容性
                if 'pattern_name' not in result:
                    result['pattern_name'] = pattern.get('name', pattern_id)
                # 添加semantic_seed
                semantic_seed = pattern.get('semantic_seed', {})
                if 'semantic_seed' not in result:
                    result['semantic_seed'] = semantic_seed.get('description', '')
                # 添加tensor_operator（用于UI显示）
                tensor_operator = pattern.get('tensor_operator', {})
                if 'tensor_operator' not in result:
                    result['tensor_operator'] = tensor_operator
                
                # 确保weights字段存在（用于UI兼容）
                if 'weights' not in result:
                    # 从tensor_operator获取weights作为fallback
                    weights = tensor_operator.get('weights', {})
                    result['weights'] = weights
                
                logger.info(f"✅ V3.0计算成功: sai={result.get('sai', 0):.4f}")
                return result
            except Exception as e:
                logger.error(f"❌ V3.0矩阵计算失败: {e}", exc_info=True)
                # 不静默回退，返回错误信息
                return {
                    'error': f'V3.0矩阵计算失败: {str(e)}',
                    'pattern_id': pattern_id,
                    'pattern_name': pattern.get('name', pattern_id),
                    'sai': 0,
                    'projection': {'E': 0, 'O': 0, 'M': 0, 'S': 0, 'R': 0},
                    'sai_warning': f'V3.0计算异常: {str(e)}'
                }
        
        # V1.0/V2.0: 使用旧的tensor_operator逻辑
        # 获取张量投影算子（模块II）
        tensor_operator = pattern.get('tensor_operator', {})
        weights = tensor_operator.get('weights', {})
        
        # 如果没有权重，返回错误（必须通过FDS-V1.1 Step 1注册）
        if not weights:
            return {
                'error': f'格局 {pattern_id} 尚未完成FDS-V1.1 Step 1注册（缺少张量投影算子）',
                'pattern_id': pattern_id,
                'pattern_name': pattern.get('name', pattern_id)
            }
        
        # 验证权重归一化（单位向量约束）
        if not tensor_operator.get('normalized', False):
            weights = self.normalize_weights(weights)
            logger.warning(f"格局 {pattern_id} 权重未归一化，已自动归一化")
        
        # 计算SAI（系统对齐指数）
        sai = 0.0
        sai_error = None
        try:
            binfo = {'day_master': day_master}
            if context:
                ctx = {
                    'luck_pillar': context.get('luck_pillar'),
                    'annual_pillar': context.get('annual_pillar'),
                    'scenario': context.get('scenario', 'default')
                }
            else:
                ctx = {'scenario': 'default'}
            
            result = self.framework.arbitrate_bazi(chart, binfo, ctx)
            
            # SAI在result['physics']['stress']['SAI']中
            physics = result.get('physics', {})
            stress = physics.get('stress', {})
            sai = stress.get('SAI', 0.0)
            
            # 如果SAI为0，记录警告并尝试诊断
            if sai == 0.0:
                # 检查是否有其他可用的应力指标
                if stress:
                    # 尝试从其他字段获取SAI
                    for key in ['sai', 'SAI', 'stress_index', 'system_alignment']:
                        if key in stress and stress[key] != 0.0:
                            sai = stress[key]
                            logger.info(f"从字段 {key} 获取SAI值: {sai}")
                            break
                
                if sai == 0.0:
                    # 诊断信息
                    diagnostic = {
                        'chart': chart,
                        'day_master': day_master,
                        'pattern_id': pattern_id,
                        'physics_keys': list(physics.keys()) if physics else [],
                        'stress_keys': list(stress.keys()) if stress else [],
                        'result_structure': list(result.keys()) if isinstance(result, dict) else 'not_dict'
                    }
                    logger.warning(
                        f"SAI计算结果为0.0，诊断信息: {diagnostic}\n"
                        f"可能的原因：1) 八字不匹配该格局 2) 计算异常 3) 结构过于稳定 4) 框架返回格式异常"
                    )
                    sai_error = "SAI计算为0，可能是格局不匹配或计算框架异常"
        except Exception as e:
            logger.error(f"计算SAI失败: {e}", exc_info=True)
            sai_error = f"SAI计算异常: {str(e)}"
            sai = 0.0
        
        # 计算五维投影（SAI × 权重）
        projection = {
            'E': sai * weights.get('E', 0.0),  # 能级轴
            'O': sai * weights.get('O', 0.0),  # 秩序轴
            'M': sai * weights.get('M', 0.0),  # 物质轴
            'S': sai * weights.get('S', 0.0),  # 应力轴
            'R': sai * weights.get('R', 0.0)   # 关联轴
        }
        
        # 获取语义意象（模块I）
        semantic_seed = pattern.get('semantic_seed', {})
        
        result_dict = {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name', pattern_id),
            'sai': sai,
            'projection': projection,
            'weights': weights,
            'semantic_seed': semantic_seed.get('description', ''),
            'tensor_operator': tensor_operator
        }
        
        # 如果SAI为0且有错误信息，添加到结果中
        if sai == 0.0 and sai_error:
            result_dict['sai_warning'] = sai_error
        
        return result_dict
    
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        权重归一化（单位向量约束）
        
        Args:
            weights: 权重字典
            
        Returns:
            归一化后的权重字典
        """
        total = sum(abs(v) for v in weights.values())
        if total == 0:
            return weights
        
        return {k: round(v / total, 4) for k, v in weights.items()}
    
    def _check_strong_root(self, stem: str, branch: str) -> bool:
        """
        检查天干是否坐强根（简化版：检查地支本气是否为天干的同类五行）
        
        Args:
            stem: 天干
            branch: 地支
            
        Returns:
            是否坐强根
        """
        # 天干五行
        stem_wuxing = {
            '甲': '木', '乙': '木',
            '丙': '火', '丁': '火',
            '戊': '土', '己': '土',
            '庚': '金', '辛': '金',
            '壬': '水', '癸': '水'
        }
        
        # 地支本气五行
        branch_wuxing = {
            '子': '水', '丑': '土', '寅': '木', '卯': '木',
            '辰': '土', '巳': '火', '午': '火', '未': '土',
            '申': '金', '酉': '金', '戌': '土', '亥': '水'
        }
        
        stem_wx = stem_wuxing.get(stem, '')
        branch_wx = branch_wuxing.get(branch, '')
        
        # 强根：地支本气与天干同五行
        if stem_wx == branch_wx:
            return True
        
        # 检查地支藏干（简化：只检查主要藏干）
        # 这里可以扩展更详细的藏干检查
        return False
    
    def _calculate_purity_score(self, sample: Dict, day_master: str) -> float:
        """
        计算样本纯度得分（基于AI分析师最新规范）
        
        Args:
            sample: 样本字典
            day_master: 日主
            
        Returns:
            纯度得分（越高越纯净）
        """
        chart = sample['chart']
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        ten_gods = sample['ten_gods']
        
        # 基础分
        score = 100.0
        
        # 加分项
        # +20分：七杀坐强根（如庚申）
        qi_sha_stems = sample.get('qi_sha_stems', [])
        for qi_sha_stem in qi_sha_stems:
            # 找到七杀所在位置
            for i, s in enumerate(stems):
                if s == qi_sha_stem:
                    # 检查对应的地支是否强根
                    if self._check_strong_root(qi_sha_stem, branches[i]):
                        score += 20
                        break  # 只加一次分
        
        # +10分：印星贴身（有通关冷却）
        yin_count = ten_gods.count('正印') + ten_gods.count('偏印')
        if yin_count > 0:
            score += yin_count * 10
        
        # 减分项
        # -15分：食伤混杂（制杀太过或干扰磁场）
        shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
        if shi_shen_count > 0:
            score -= shi_shen_count * 15
        
        # -15分：财星党杀（增加应力风险）
        cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
        if cai_count > 0:
            score -= cai_count * 15
        
        # -10分：地支有刑/冲/穿（结构不稳）
        clash_pairs = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
                      ('辰', '戌'), ('巳', '亥')]
        harm_pairs = [('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'),
                     ('申', '亥'), ('酉', '戌')]
        
        has_clash = False
        has_harm = False
        for i, b1 in enumerate(branches):
            for j, b2 in enumerate(branches[i+1:], i+1):
                if (b1, b2) in clash_pairs or (b2, b1) in clash_pairs:
                    has_clash = True
                if (b1, b2) in harm_pairs or (b2, b1) in harm_pairs:
                    has_harm = True
        
        if has_clash or has_harm:
            score -= 10
        
        return score
    
    def _detect_singularity(self, sample: Dict, day_master: str) -> Tuple[bool, str]:
        """
        检测是否为奇点样本（基于AI分析师最新规范）
        
        Args:
            sample: 样本字典
            day_master: 日主
            
        Returns:
            (是否为奇点, 奇点类型)
        """
        chart = sample['chart']
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        ten_gods = sample['ten_gods']
        
        # 获取羊刃地支
        yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        yang_ren_branch = yang_ren_map.get(day_master)
        
        # 1. 能量溢出：地支羊刃数量 >= 3（如：地支三卯）
        yang_ren_count = branches.count(yang_ren_branch) if yang_ren_branch else 0
        if yang_ren_count >= 3:
            return True, "X1-聚变临界型（地支三刃）"
        
        # 2. 高压临界：天干透出2个或以上七杀，且四柱无食神（制）无印星（化），纯粹攻身
        qi_sha_count = ten_gods.count('七杀')
        yin_count = ten_gods.count('正印') + ten_gods.count('偏印')
        shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
        
        if qi_sha_count >= 2 and yin_count == 0 and shi_shen_count == 0:
            return True, "X2-结构高压型（众杀攻身无制）"
        
        return False, ""
    
    def select_samples(self, pattern_id: str, target_count: int = 500, 
                      progress_callback: Optional[callable] = None,
                      output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        按照FDS-V1.1 Step 2的数据选择标准进行样本海选（升级版：纯度排序+奇点捕获）
        
        Args:
            pattern_id: 格局ID
            target_count: 目标样本数量（默认500，用于Tier A标准集）
            progress_callback: 进度回调函数 (current, total, stats)
            output_dir: 输出目录（如果提供，将保存两个JSON文件）
            
        Returns:
            包含standard_set和singularities的字典
        """
        # 获取格局信息
        pattern = self.get_pattern_by_id(pattern_id)
        if not pattern:
            logger.error(f"格局 {pattern_id} 不存在")
            return []
        
        # 获取数据选择标准
        data_criteria = pattern.get('audit_trail', {}).get('data_selection_criteria', {})
        if not data_criteria:
            logger.error(f"格局 {pattern_id} 缺少数据选择标准")
            return []
        
        # 初始化生成器
        engine = SyntheticBaziEngine()
        bazi_gen = engine.generate_all_bazi()
        
        candidates = []
        total_scanned = 0
        stats = {
            'scanned': 0,
            'matched': 0,
            'rejected_month_lock': 0,
            'rejected_stem_reveal': 0,
            'rejected_purity': 0
        }
        
        logger.info(f"开始样本海选：格局={pattern_id}，目标={target_count}例，全量扫描518,400个样本")
        
        # 严格全量扫描：必须扫描所有518,400个样本
        for chart in bazi_gen:
            total_scanned += 1
            stats['scanned'] = total_scanned
            
            # 进度回调（每10,000个样本或每5%进度）
            if progress_callback and (total_scanned % 10000 == 0 or total_scanned % 25920 == 0):
                progress_callback(total_scanned, 518400, stats)
            
            # 注意：不提前退出，必须扫描全部518,400个样本
            
            # 提取基本信息
            year_pillar, month_pillar, day_pillar, hour_pillar = chart
            day_master = day_pillar[0]
            month_branch = month_pillar[1]
            
            # 1. 月令锁：月支本气必须为日主之帝旺（即羊刃）
            life_stage = TWELVE_LIFE_STAGES.get((day_master, month_branch))
            if life_stage != '帝旺':
                stats['rejected_month_lock'] += 1
                continue
            
            # 2. 天干透杀：天干必须透出七杀，且七杀必须有根
            stems = [year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0]]
            branches = [year_pillar[1], month_pillar[1], day_pillar[1], hour_pillar[1]]
            
            # 检查天干是否有七杀
            qi_sha_stems = []
            for i, stem in enumerate(stems):
                if i == 2:  # 跳过日主
                    continue
                ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
                if ten_god == '七杀':
                    qi_sha_stems.append((i, stem))
            
            if not qi_sha_stems:
                stats['rejected_stem_reveal'] += 1
                continue
            
            # 检查七杀是否有根
            has_root = False
            for _, qi_sha_stem in qi_sha_stems:
                # 检查自坐
                pillar_idx = qi_sha_stems[0][0]
                if pillar_idx < len(branches):
                    branch = branches[pillar_idx]
                    hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                    for hidden_stem, weight in hidden_stems:
                        if hidden_stem == qi_sha_stem and weight >= 5:  # 主气或中气
                            has_root = True
                            break
                
                # 检查其他地支
                if not has_root:
                    for branch in branches:
                        hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                        for hidden_stem, weight in hidden_stems:
                            if hidden_stem == qi_sha_stem and weight >= 5:
                                has_root = True
                                break
                        if has_root:
                            break
                
                if has_root:
                    break
            
            if not has_root:
                stats['rejected_stem_reveal'] += 1
                continue
            
            # 3. 清纯度过滤：剔除重食伤制杀、重财党杀
            ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
            
            # 统计食伤和财星数量
            shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
            cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
            qi_sha_count = ten_gods.count('七杀')
            
            # 剔除重食伤制杀（这会变成A-02食神制杀）
            if shi_shen_count >= 2 and qi_sha_count >= 1:
                stats['rejected_purity'] += 1
                continue
            
            # 剔除重财党杀（这会导致应力轴S爆表）
            if cai_count >= 2 and qi_sha_count >= 1:
                stats['rejected_purity'] += 1
                continue
            
            # 通过所有筛选条件
            candidates.append({
                'chart': chart,
                'day_master': day_master,
                'month_branch': month_branch,
                'qi_sha_stems': [s for _, s in qi_sha_stems],
                'ten_gods': ten_gods
            })
            stats['matched'] += 1
        
        # 验证是否扫描了全部样本
        if total_scanned < 518400:
            logger.warning(f"⚠️ 只扫描了 {total_scanned} 个样本，未达到全量518,400个")
        else:
            logger.info(f"✅ 已扫描全部518,400个样本")
        
        logger.info(f"Step A完成：扫描={total_scanned}，匹配={len(candidates)}，目标={target_count}")
        logger.info(f"统计：月令锁拒绝={stats['rejected_month_lock']}，透杀拒绝={stats['rejected_stem_reveal']}，纯度拒绝={stats['rejected_purity']}")
        
        # ========== Step B: 奇点捕获 (Tier X) ==========
        logger.info("=" * 70)
        logger.info("Step B: 奇点捕获 (Tier X)")
        logger.info("=" * 70)
        
        singularities = []
        standard_candidates = []
        
        for sample in candidates:
            day_master = sample['day_master']
            is_singularity, singularity_type = self._detect_singularity(sample, day_master)
            
            if is_singularity:
                sample['singularity_type'] = singularity_type
                sample['purity_score'] = self._calculate_purity_score(sample, day_master)
                singularities.append(sample)
            else:
                standard_candidates.append(sample)
        
        logger.info(f"✅ 发现奇点样本 {len(singularities)} 个，已隔离")
        logger.info(f"✅ 标准候选样本 {len(standard_candidates)} 个")
        
        # ========== Step C: 标准集优选 (Tier A) ==========
        logger.info("=" * 70)
        logger.info("Step C: 标准集优选 (Tier A) - 纯度加权排序")
        logger.info("=" * 70)
        
        # 计算纯度得分并排序
        for sample in standard_candidates:
            day_master = sample['day_master']
            sample['purity_score'] = self._calculate_purity_score(sample, day_master)
        
        # 按纯度得分降序排序
        standard_candidates.sort(key=lambda x: x['purity_score'], reverse=True)
        
        # 截取前target_count个作为Tier A标准集
        if len(standard_candidates) > target_count:
            standard_set = standard_candidates[:target_count]
            logger.info(f"✅ 从 {len(standard_candidates)} 个候选样本中，按纯度排序选取前 {target_count} 个作为Tier A标准集")
        else:
            standard_set = standard_candidates
            logger.info(f"✅ 候选样本 {len(standard_candidates)} 个（少于目标 {target_count}），全部作为Tier A标准集")
        
        # 输出统计
        if standard_set:
            avg_purity = sum(s['purity_score'] for s in standard_set) / len(standard_set)
            max_purity = max(s['purity_score'] for s in standard_set)
            min_purity = min(s['purity_score'] for s in standard_set)
            logger.info(f"Tier A纯度统计：平均={avg_purity:.2f}，最高={max_purity:.2f}，最低={min_purity:.2f}")
        
        # ========== 保存结果 ==========
        result = {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name_cn', pattern_id),
            'total_scanned': total_scanned,
            'tier_a': {
                'count': len(standard_set),
                'samples': standard_set
            },
            'tier_x': {
                'count': len(singularities),
                'samples': singularities
            },
            'stats': stats
        }
        
        # 如果提供了输出目录，保存文件
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存Tier A标准集
            standard_file = output_dir / f"QGA_{pattern_id}_TierA_Standard.json"
            with open(standard_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern.get('name_cn', pattern_id),
                    'tier': 'A',
                    'description': '标准纯净集（Tier A）- 最教科书级的样本',
                    'count': len(standard_set),
                    'samples': standard_set
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Tier A标准集已保存: {standard_file}")
            
            # 保存Tier X奇点集
            if singularities:
                singularity_file = output_dir / f"QGA_{pattern_id}_TierX_Singularity.json"
                with open(singularity_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'pattern_id': pattern_id,
                        'pattern_name': pattern.get('name_cn', pattern_id),
                        'tier': 'X',
                        'description': '奇点集（Tier X）- 极端样本，蕴含新的物理定律',
                        'count': len(singularities),
                        'samples': singularities
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Tier X奇点集已保存: {singularity_file}")
        
        logger.info("=" * 70)
        logger.info(f"✅ 样本海选完成：Tier A={len(standard_set)}个，Tier X={len(singularities)}个")
        logger.info("=" * 70)
        
        return result

