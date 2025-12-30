import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class LogicRegistry:
    """The Great Librarian: Ensures no algorithm is ever forgotten."""
    
    _instance = None
    _manifest = {}

    # [QGA V16.0] 四层能级定义
    LAYERS = {
        "INFRA": "基础设施",
        "ALGO": "核心算子",
        "MODEL": "物理模型",
        "TOPIC": "业务专题"
    }

    # [V4.2.6] 全局逻辑路由表：连接 Registry ID 与 引擎内部逻辑 ID
    _LOGIC_ROUTING = {
        "MOD_101": ["SHANG_GUAN_JIAN_GUAN"],
        "MOD_102": ["SHANG_GUAN_XI_SHI_SHANG"],
        "MOD_103": ["SHANG_GUAN_YONG_CAI"],
        "MOD_104": ["SHANG_GUAN_SHANG_JIN"],
        "MOD_105": ["YANG_REN_JIA_SHA"],
        "MOD_106": ["XIAO_SHEN_DUO_SHI"],
        "MOD_107": ["CAI_GUAN_XIANG_SHENG_V4"],
        "MOD_108": ["SHANG_GUAN_PEI_YIN"],
        "MOD_109": ["SHI_SHEN_ZHI_SHA"],
        "MOD_110": ["PGB_ULTRA_FLUID", "PGB_BRITTLE_TITAN"],
        "MOD_111": ["CYGS_COLLAPSE"],
        "MOD_112": ["HGFG_TRANSMUTATION"],
        "MOD_113": ["SSSC_AMPLIFIER"],
        "MOD_114": ["JLTG_CORE_ENERGY"],
        "MOD_115": ["SSZS_PULSE_INTERCEPTION"],
        "MOD_116": ["GYPS_RECTIFIER_BRIDGE"],
        "MOD_117": ["CWJG_FEEDBACK_LOOP"],
        "MOD_119": ["CE_FLARE_DISCHARGE"],
        "MOD_121": ["YGZJ_MONOPOLE_ENERGY"],
        "MOD_122": ["YHGS_THERMODYNAMIC_ENTROPY"],
        "MOD_123": ["LYKG_LC_SELF_LOCKING"],
        "MOD_124": ["JJGG_QUANTUM_TUNNELING"],
        "MOD_125": ["TYKG_PHASE_RESONANCE"],
        "MOD_126": ["CWJS_QUANTUM_TRANSITION"],
        "MOD_127": ["MHGG_REVERSION_DYNAMICS"],
        "MOD_128": ["GXYG_VIRTUAL_GAP"],
        "MOD_129": ["MBGS_STORAGE_POTENTIAL"],
        "MOD_130": ["ZHSG_MIXED_EXCITATION"],
        "MOD_131": ["MBGS_STORAGE_POTENTIAL"], # Jin Shen Sub-space
        "MOD_132": ["MBGS_STORAGE_POTENTIAL"], # Kui Gang Sub-space
        "MOD_133": ["MBGS_STORAGE_POTENTIAL"], # Four Graves Sub-space
        "MOD_134": ["ZHSG_MIXED_EXCITATION"], # TSG Sub-space
        "MOD_135": ["ZHSG_MIXED_EXCITATION"]  # YQG Sub-space
    }

    # [V4.2.6] 语义别名映射表
    ALIASES = {
        "CAI_GUAN_XIANG_SHENG": "MOD_107",
        "SHI_SHEN_ZHI_SHA": "MOD_115",
        "PGB_SUPER_FLUID_LOCK": "MOD_110",
        "伤官见官": "MOD_101",
        "伤官伤尽": "MOD_104",
        "食神制杀": "MOD_115",
        "财官相生": "MOD_107",
        "超流锁定": "MOD_110",
        "从儿格": "MOD_119",
        "官印相生": "MOD_116",
        "财官联动": "MOD_117",
        "羊刃单极": "MOD_121",
        "调候熵增": "MOD_122",
        "禄位自锁": "MOD_123",
        "量子隧道": "MOD_124",
        "专旺共振": "MOD_125",
        "弃命相变": "MOD_126",
        "还原动力": "MOD_127",
        "拱夹虚拟": "MOD_128",
        "墓库势能": "MOD_129",
        "杂气激发": "MOD_130",
        "金神子态": "MOD_131",
        "魁罡算子": "MOD_132",
        "四库全齐": "MOD_133",
        "透干激发": "MOD_134",
        "月令余气": "MOD_135"
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogicRegistry, cls).__new__(cls)
            cls._instance._load_manifest()
        return cls._instance

    def _load_manifest(self):
        path = os.path.join(os.path.dirname(__file__), 'logic_manifest.json')
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self._manifest = json.load(f)
                logger.info(f"✅ Core Logic Manifest loaded: V{self._manifest.get('version')}")
            else:
                logger.warning("⚠️ logic_manifest.json not found. Using empty registry.")
        except Exception as e:
            logger.error(f"❌ Failed to load logic manifest: {e}")

    def get_logic_routing(self) -> Dict[str, List[str]]:
        """获取全量引擎映射表。"""
        return self._LOGIC_ROUTING

    def resolve_logic_id(self, input_id: str) -> Tuple[str, List[str]]:
        """
        [V4.2.6] 全面识别逻辑。将输入解析为 (Registry_Full_ID, Logic_ID_List)。
        优先级：1. 显式 Registry ID 2. 语义别名 3. 模糊名称匹配
        """
        modules = self._manifest.get('modules', {})
        
        # 1. 尝试 MOD_xxx 前缀匹配
        if input_id.startswith("MOD_"):
            parts = input_id.split("_")
            prefix = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else input_id
            
            # 从 manifest 查找完整 ID (带版本描述的那个)
            registry_id = input_id
            for m_id in modules:
                if m_id.startswith(prefix):
                    registry_id = m_id
                    break
            
            return registry_id, self._LOGIC_ROUTING.get(prefix, [input_id])
            
        # 2. 语义别名匹配
        target_prefix = self.ALIASES.get(input_id)
        if target_prefix:
            # 递归解析前缀
            return self.resolve_logic_id(target_prefix)
            
        # 3. 如果还是没找到，尝试在所有 MOD 的名称里搜关键字
        for m_id, m_data in modules.items():
            if input_id in m_data.get('name', ''):
                parts = m_id.split("_")
                prefix = f"{parts[0]}_{parts[1]}"
                return m_id, self._LOGIC_ROUTING.get(prefix, [input_id])
                
        # 4. 彻底没有映射，保持原样回退
        return "UNKNOWN_REGISTRY", [input_id]

    def get_items_by_layer(self, layer: str) -> List[Dict[str, Any]]:
        """[V16.0] 按层级获取注册项，主要用于 UI 轨道渲染。"""
        modules = self._manifest.get('modules', {})
        items = []
        for mid, mdata in modules.items():
            if mdata.get('layer') == layer and mdata.get('active', True):
                m_copy = mdata.copy()
                m_copy['reg_id'] = mid
                # 优先级: name_cn > name
                m_copy['display_name'] = mdata.get('name_cn', mdata.get('name', mid))
                items.append(m_copy)
        return sorted(items, key=lambda x: x.get('reg_id', ''))

    def get_dependencies(self, item_id: str) -> List[str]:
        """[V16.0] 获取指定专题的物理依赖链（算法和模型）。"""
        item = self._manifest.get('modules', {}).get(item_id, {})
        return item.get('dependencies', [])

    def get_rule(self, rule_id: str) -> Dict[str, Any]:
        return self._manifest.get('registry', {}).get(rule_id, {})

    def get_all_active_rules(self) -> Dict[str, Dict[str, Any]]:
        registry = self._manifest.get('registry', {})
        return {k: v for k, v in registry.items() if v.get('status') == 'ACTIVE'}

    def get_themes(self) -> Dict[str, Any]:
        """Retrieves and returns the high-level themes from the manifest."""
        return self._manifest.get('themes', {})

    def get_active_modules(self, theme_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves active UI modules from the manifest, optionally filtered by theme.
        If theme has a registry_path, loads modules from the registry file.
        Otherwise, loads from manifest modules.
        Returns a list of module dictionaries including their ID.
        """
        # Check if theme has a registry_path
        themes = self._manifest.get('themes', {})
        theme_data = themes.get(theme_id) if theme_id else None
        
        if theme_data and theme_data.get('registry_path'):
            # Load modules from registry file
            try:
                from core.registry_loader import RegistryLoader
                from pathlib import Path
                import os
                
                registry_path = Path(__file__).parent.parent / theme_data['registry_path']
                if registry_path.exists():
                    loader = RegistryLoader(registry_path=registry_path, theme_id=theme_id)
                    registry = loader.registry
                    
                    if registry and 'patterns' in registry:
                        active_list = []
                        for pattern_id, pattern_data in registry['patterns'].items():
                            if pattern_data.get('active', True):
                                # Convert pattern structure to module structure
                                module_dict = {
                                    'id': pattern_id,
                                    'name': pattern_data.get('name', pattern_id),
                                    'name_cn': pattern_data.get('name_cn', pattern_data.get('name', pattern_id)),
                                    'name_en': pattern_data.get('name_en', pattern_data.get('name', pattern_id)),
                                    'icon': pattern_data.get('icon', '🔧'),
                                    'description': pattern_data.get('description', ''),
                                    'goal': pattern_data.get('goal', ''),
                                    'outcome': pattern_data.get('outcome', ''),
                                    'layer': pattern_data.get('layer', 'FUNDAMENTAL'),
                                    'priority': pattern_data.get('priority', 500),
                                    'linked_rules': pattern_data.get('linked_rules', []),
                                    'linked_metrics': pattern_data.get('linked_metrics', []),
                                    'origin_trace': pattern_data.get('origin_trace', []),
                                    'fusion_type': pattern_data.get('fusion_type', 'CORE_MODULE'),
                                    'class': pattern_data.get('class', ''),
                                    'theme': theme_id,
                                    'active': pattern_data.get('active', True),
                                    'version': pattern_data.get('version', '1.0'),
                                    'category': pattern_data.get('category', 'FUNDAMENTAL'),
                                    'subject_id': pattern_data.get('subject_id', pattern_id),
                                    # Include full pattern data for detailed view
                                    'pattern_data': pattern_data
                                }
                                active_list.append(module_dict)
                        
                        # Sort by key (MOD_00, MOD_01...)
                        return sorted(active_list, key=lambda x: x['id'])
                    else:
                        logger.warning(f"注册表中没有找到 patterns: {registry_path}")
                else:
                    logger.warning(f"注册表文件不存在: {registry_path}")
            except Exception as e:
                logger.error(f"从注册表加载模块失败: {e}")
                # Fall back to manifest modules
        
        # Fallback: Load from manifest modules
        modules = self._manifest.get('modules', {})
        active_list = []
        for m_id, m_data in modules.items():
            # [V4.2.6] Ensure every module has a version-pinned ID
            if m_data.get('active', True):
                # Filter by theme if requested
                if theme_id and m_data.get('theme') != theme_id:
                    continue
                    
                m_copy = m_data.copy()
                m_copy['id'] = m_id
                active_list.append(m_copy)
        
        # Sort by key (MOD_00, MOD_01...)
        return sorted(active_list, key=lambda x: x['id'])

    def verify_conformance(self, active_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cross-checks current analysis results against the manifest to detect 'Logic Loss'.
        """
        active_ids = {i.get('id') for i in active_interactions}
        manifest_rules = self.get_all_active_rules()
        
        missing = []
        for r_id, r_info in manifest_rules.items():
            # This is a simplified check: if a rule ID from manifest is missing in current stack
            # In a real sniffer, we would re-evaluate the conditions.
            pass
            
        return {
            "conformance_score": 1.0, # Placeholder
            "missing_rules": missing
        }

    @property
    def version(self):
        return self._manifest.get('version', '0.0.0')

    @property
    def manifest(self):
        return self._manifest

    def update_module_audit_parameters(self, module_id: str, audit_parameters: Dict[str, Any]) -> bool:
        """
        更新模块的审计参数调优结果到注册表
        
        Args:
            module_id: 模块ID (如 "MOD_101_SGJG_FAILURE")
            audit_parameters: 审计参数调优结果，包含：
                - step_a_tuning: Step A的参数调优（如命中率阈值调整）
                - step_d_tuning: Step D的参数调优（如stress_tensor权重修正）
                - evolution_log: 演化日志
        
        Returns:
            bool: 是否成功更新
        """
        try:
            modules = self._manifest.get('modules', {})
            if module_id not in modules:
                logger.warning(f"模块 {module_id} 不存在于注册表中")
                return False
            
            module = modules[module_id]
            
            # 初始化audit_parameters字段（如果不存在）
            if 'audit_parameters' not in module:
                module['audit_parameters'] = {}
            
            # 更新Step A调优结果
            if 'step_a_tuning' in audit_parameters:
                module['audit_parameters']['step_a_tuning'] = audit_parameters['step_a_tuning']
            
            # 更新Step D调优结果
            if 'step_d_tuning' in audit_parameters:
                module['audit_parameters']['step_d_tuning'] = audit_parameters['step_d_tuning']
            
            # 更新演化日志
            if 'evolution_log' in audit_parameters:
                if 'evolution_history' not in module['audit_parameters']:
                    module['audit_parameters']['evolution_history'] = []
                module['audit_parameters']['evolution_history'].append(audit_parameters['evolution_log'])
            
            # 更新最后审计时间
            module['audit_parameters']['last_audit_date'] = audit_parameters.get('audit_date', 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # 保存到文件
            return self._save_manifest()
            
        except Exception as e:
            logger.error(f"更新模块审计参数失败: {e}")
            return False
    
    def _save_manifest(self) -> bool:
        """保存manifest到文件"""
        try:
            import os
            from datetime import datetime
            path = os.path.join(os.path.dirname(__file__), 'logic_manifest.json')
            
            # 创建备份
            backup_path = f"{path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(path):
                import shutil
                shutil.copy2(path, backup_path)
                logger.info(f"已创建备份: {backup_path}")
            
            # 保存更新后的manifest
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._manifest, f, ensure_ascii=False, indent=4)
            
            logger.info(f"✅ 注册表已更新: {path}")
            return True
            
        except Exception as e:
            logger.error(f"保存注册表失败: {e}")
            return False