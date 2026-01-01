"""
🎛️ Registry Management Controller
==================================
Controller for the Quantum Registry Management System.
Handles reading and managing system manifests and pattern registries.

MVC: Controller Layer
View: ui/pages/registry_admin.py
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGIC_MANIFEST_PATH = PROJECT_ROOT / "core" / "logic_manifest.json"
PATTERN_REGISTRY_PATH = PROJECT_ROOT / "core" / "subjects" / "holographic_pattern" / "registry.json"

logger = logging.getLogger(__name__)


class RegistryManagementController:
    """
    Controller for the Quantum Registry Management System.
    Handles reading and managing system manifests and pattern registries.
    """

    def __init__(self):
        self.manifest_data = self._load_json(LOGIC_MANIFEST_PATH)
        self.pattern_data = self._load_json(PATTERN_REGISTRY_PATH)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Helper to load JSON safely."""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.error(f"File not found: {path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return {}

    def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system stats."""
        modules = self.manifest_data.get('modules', {})
        patterns = self.pattern_data.get('patterns', {})
        
        active_modules = sum(1 for m in modules.values() if m.get('active', False))
        active_patterns = sum(1 for p in patterns.values() if p.get('active', False))
        
        return {
            "system_version": self.manifest_data.get('version', 'Unknown'),
            "system_id": self.manifest_data.get('system_id', 'Unknown'),
            "description": self.manifest_data.get('description', ''),
            "total_modules": len(modules),
            "active_modules": active_modules,
            "total_patterns": len(patterns),
            "active_patterns": active_patterns,
            "update_date": self.pattern_data.get('meta', {}).get('updated', 'Unknown')
        }

    def get_themes(self) -> Dict[str, Any]:
        """Get all registered themes."""
        return self.manifest_data.get('themes', {})

    def get_all_layers(self) -> List[str]:
        """Get all unique layers from modules."""
        modules = self.manifest_data.get('modules', {})
        layers = set()
        for mod in modules.values():
            layer = mod.get('layer')
            if layer:
                layers.add(layer)
        return sorted(list(layers))

    def get_modules_by_theme(self, theme_id: str) -> List[Dict[str, Any]]:
        """Get all modules belonging to a specific theme."""
        modules = self.manifest_data.get('modules', {})
        result = []
        for mod_id, info in modules.items():
            if info.get('theme') == theme_id:
                result.append({
                    'id': mod_id,
                    'name': info.get('name', ''),
                    'active': info.get('active', False),
                    'layer': info.get('layer', 'Unknown')
                })
        return result

    def get_patterns_by_theme(self, theme_id: str) -> List[Dict[str, Any]]:
        """Get all patterns belonging to a specific theme.
        
        For HOLOGRAPHIC_PATTERN theme, returns all patterns from the holographic registry.
        """
        result = []
        
        # For HOLOGRAPHIC_PATTERN theme, return all patterns from pattern_data
        if theme_id == "HOLOGRAPHIC_PATTERN":
            patterns = self.pattern_data.get('patterns', {})
            for pat_id, info in patterns.items():
                result.append({
                    'id': pat_id,
                    'name': info.get('name', ''),
                    'name_cn': info.get('name_cn', ''),
                    'active': info.get('active', False),
                    'category': info.get('category', 'Unknown'),
                    'icon': info.get('icon', '🌌')
                })
        
        return result

    def get_modules_dataframe_data(self) -> List[Dict[str, Any]]:
        """Prepare module data for tabular display."""
        modules = self.manifest_data.get('modules', {})
        data = []
        for mod_id, info in modules.items():
            data.append({
                "ID": mod_id,
                "Name": info.get('name', ''),
                "Icon": info.get('icon', ''),
                "Layer": info.get('layer', 'Unknown'),
                "Status": "✅ Active" if info.get('active') else "⛔ Inactive",
                "Theme": info.get('theme', ''),
                "Description": info.get('description', '')[:100] + '...' if len(info.get('description', '')) > 100 else info.get('description', '')
            })
        return data

    def get_patterns_dataframe_data(self) -> List[Dict[str, Any]]:
        """Prepare pattern data for tabular display."""
        patterns = self.pattern_data.get('patterns', {})
        data = []
        for pid, info in patterns.items():
            meta = info.get('meta_info', {})
            compliance = meta.get('compliance', 'N/A')
            
            # Check compliance status (FDS-V3.0 is preferred)
            if compliance.startswith("FDS-V3"):
                comp_status = "✅"  # V3.0 is fully compliant
                comp_display = f"✅ {compliance} (最新标准)"
            elif (compliance.startswith("FDS-V2") or
                  compliance.startswith("FDS-V1.5") or 
                  compliance.startswith("FDS-V1.6") or 
                  compliance.startswith("FDS-V1.7")):
                comp_status = "⚠️"  # Legacy versions (acceptable but deprecated)
                comp_display = f"⚠️ {compliance} (已废弃)"
            else:
                comp_status = "❌"  # Non-compliant
                comp_display = f"❌ {compliance} (不合规)"
            
            data.append({
                "ID": pid,
                "Name": meta.get('name', info.get('name', '')),
                "CN Name": meta.get('chinese_name', info.get('name_cn', '')),
                "Category": meta.get('category', info.get('category', 'N/A')),
                "Compliance": comp_display,
                "Version": info.get('version', meta.get('version', '')),
                "Sub-Patterns": len(info.get('sub_patterns_registry', [])),
            })
        return data

    def get_module_details(self, module_id: str) -> Dict[str, Any]:
        """Get raw details for a module."""
        return self.manifest_data.get('modules', {}).get(module_id, {})

    def get_pattern_details(self, pattern_id: str) -> Dict[str, Any]:
        """Get raw details for a pattern."""
        return self.pattern_data.get('patterns', {}).get(pattern_id, {})

    def get_system_health(self) -> Dict[str, float]:
        """Calculate system health metrics."""
        modules = self.manifest_data.get('modules', {})
        patterns = self.pattern_data.get('patterns', {})
        themes = self.manifest_data.get('themes', {})
        
        # Module coverage
        total_modules = len(modules)
        active_modules = sum(1 for m in modules.values() if m.get('active', False))
        module_coverage = active_modules / total_modules if total_modules > 0 else 0
        
        # Pattern coverage
        total_patterns = len(patterns)
        active_patterns = sum(1 for p in patterns.values() if p.get('active', False))
        pattern_coverage = active_patterns / total_patterns if total_patterns > 0 else 0
        
        # Theme utilization
        themes_with_modules = set()
        for mod in modules.values():
            theme = mod.get('theme')
            if theme and mod.get('active', False):
                themes_with_modules.add(theme)
        theme_utilization = len(themes_with_modules) / len(themes) if themes else 0
        
        # Compliance rate (only FDS-V3.0 counts as fully compliant)
        compliant_patterns = 0
        for p in patterns.values():
            meta = p.get('meta_info', {})
            compliance = meta.get('compliance', '')
            if compliance.startswith('FDS-V3'):  # Only V3.0 is fully compliant
                compliant_patterns += 1
        compliance_rate = compliant_patterns / total_patterns if total_patterns > 0 else 0
        
        return {
            'module_coverage': module_coverage,
            'pattern_coverage': pattern_coverage,
            'theme_utilization': theme_utilization,
            'compliance_rate': compliance_rate
        }

    def refresh_data(self):
        """Reload data from disk."""
        self.manifest_data = self._load_json(LOGIC_MANIFEST_PATH)
        self.pattern_data = self._load_json(PATTERN_REGISTRY_PATH)

    # ==================== CRUD Operations ====================
    
    def update_module_status(self, module_id: str, active: bool) -> bool:
        """Update the active status of a module."""
        try:
            if module_id in self.manifest_data.get('modules', {}):
                self.manifest_data['modules'][module_id]['active'] = active
                self._save_manifest()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating module status: {e}")
            return False

    def update_pattern_compliance(self, pattern_id: str, compliance: str) -> bool:
        """Update the compliance field of a pattern."""
        try:
            if pattern_id in self.pattern_data.get('patterns', {}):
                if 'meta_info' not in self.pattern_data['patterns'][pattern_id]:
                    self.pattern_data['patterns'][pattern_id]['meta_info'] = {}
                self.pattern_data['patterns'][pattern_id]['meta_info']['compliance'] = compliance
                self._save_pattern_registry()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating pattern compliance: {e}")
            return False

    def _save_manifest(self) -> bool:
        """Save manifest data to disk."""
        try:
            with open(LOGIC_MANIFEST_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.manifest_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
            return False

    def _save_pattern_registry(self) -> bool:
        """Save pattern registry to disk."""
        try:
            with open(PATTERN_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.pattern_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving pattern registry: {e}")
            return False

    # ==================== Search & Query ====================
    
    def search_modules(self, query: str) -> List[Dict[str, Any]]:
        """Search modules by name, ID, or description."""
        query = query.lower()
        results = []
        for mod_id, info in self.manifest_data.get('modules', {}).items():
            if (query in mod_id.lower() or 
                query in info.get('name', '').lower() or 
                query in info.get('description', '').lower()):
                results.append({
                    'id': mod_id,
                    'name': info.get('name', ''),
                    'active': info.get('active', False),
                    'layer': info.get('layer', 'Unknown'),
                    'theme': info.get('theme', '')
                })
        return results

    def search_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Search patterns by name or ID."""
        query = query.lower()
        results = []
        for pid, info in self.pattern_data.get('patterns', {}).items():
            if (query in pid.lower() or 
                query in info.get('name', '').lower() or 
                query in info.get('name_cn', '').lower()):
                results.append({
                    'id': pid,
                    'name': info.get('name', ''),
                    'name_cn': info.get('name_cn', ''),
                    'category': info.get('category', ''),
                    'active': info.get('active', False)
                })
        return results

    def get_modules_by_layer(self, layer: str) -> List[Dict[str, Any]]:
        """Get all modules in a specific layer."""
        return [
            {'id': mod_id, **info}
            for mod_id, info in self.manifest_data.get('modules', {}).items()
            if info.get('layer') == layer
        ]

    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all patterns in a specific category."""
        return [
            {'id': pid, **info}
            for pid, info in self.pattern_data.get('patterns', {}).items()
            if info.get('category') == category
        ]
